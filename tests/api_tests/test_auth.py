import os
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient
from authlib.jose import JsonWebToken
from fastmcp.server.auth.providers.jwt import JWTVerifier, RSAKeyPair

from api import app


class AuthTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.keys = RSAKeyPair.generate()
        cls.issuer = "https://example.auth0.com/"
        cls.audience = "https://expense-tracker-api"

    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        env = patch.dict(os.environ, {
            "AUTH0_DOMAIN": "example.auth0.com",
            "AUTH0_AUDIENCE": self.audience,
            "EXPENSE_TRACKER_DB": str(Path(directory.name) / "test.db"),
        })
        env.start()
        self.addCleanup(env.stop)
        verifier = JWTVerifier(public_key=self.keys.public_key, issuer=self.issuer, audience=self.audience, algorithm="RS256")
        mocked = patch("tracker.api.auth.verifier", return_value=verifier)
        mocked.start()
        self.addCleanup(mocked.stop)
        self.client = TestClient(app)

    def token(self, **kwargs):
        values = {"subject": "auth0|alice", "issuer": self.issuer, "audience": self.audience,
                  "scopes": ["read:expenses", "write:expenses"]}
        values.update(kwargs)
        return self.keys.create_token(**values)

    def get(self, token):
        return self.client.get("/api/expenses", headers={"Authorization": f"Bearer {token}"})

    def test_valid_and_invalid_tokens(self):
        self.assertEqual(self.client.get("/api/expenses").status_code, 401)
        self.assertEqual(self.get(self.token()).status_code, 200)
        self.assertEqual(self.get(self.token(issuer="https://wrong.example/")).status_code, 401)
        self.assertEqual(self.get(self.token(audience="https://wrong.example/")).status_code, 401)
        self.assertEqual(self.get(self.token(expires_in_seconds=-1)).status_code, 401)
        self.assertEqual(self.get(self.token(subject="service@clients")).status_code, 401)
        self.assertEqual(self.get(self.token(scopes=["write:expenses"])).status_code, 403)
        self.assertEqual(self.get(self.token(additional_claims={"nbf": 4102444800})).status_code, 401)
        other_keys = RSAKeyPair.generate()
        self.assertEqual(self.get(other_keys.create_token(issuer=self.issuer, audience=self.audience)).status_code, 401)
        no_expiry = JsonWebToken(["RS256"]).encode({"alg": "RS256"}, {
            "iss": self.issuer, "sub": "auth0|alice", "aud": self.audience,
            "iat": 1, "scope": "read:expenses",
        }, self.keys.private_key.get_secret_value()).decode()
        self.assertEqual(self.get(no_expiry).status_code, 401)

    def test_verified_subject_controls_owner(self):
        alice = {"Authorization": f"Bearer {self.token()}"}
        bob = {"Authorization": f"Bearer {self.token(subject='auth0|bob')}"}
        expense = self.client.post("/api/expenses", headers=alice, json={"amount": "5", "category": "Food"}).json()
        self.assertEqual(self.client.get("/api/expenses", headers=bob).json(), [])
        self.assertEqual(self.client.delete(f"/api/expenses/{expense['id']}", headers=bob).status_code, 404)
        self.assertEqual(self.client.get("/api/expenses", headers=alice).json(), [expense])

    def test_legacy_database_is_not_modified(self):
        path = os.environ["EXPENSE_TRACKER_DB"]
        with closing(sqlite3.connect(path)) as connection, connection:
            connection.execute("CREATE TABLE expenses (id INTEGER PRIMARY KEY, category TEXT)")
            connection.execute("INSERT INTO expenses (category) VALUES ('legacy')")
        with self.assertRaisesRegex(RuntimeError, "legacy unowned data"):
            self.get(self.token())
        with closing(sqlite3.connect(path)) as connection:
            self.assertEqual(connection.execute("SELECT category FROM expenses").fetchall(), [("legacy",)])
            self.assertEqual(connection.execute("PRAGMA user_version").fetchone()[0], 0)


if __name__ == "__main__":
    unittest.main()
