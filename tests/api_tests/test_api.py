import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient
from fastapi import Header

from api import app
from tracker.api.auth import require_owner


class ApiTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        environment = patch.dict(os.environ, {"EXPENSE_TRACKER_DB": str(Path(directory.name) / "test.db")})
        environment.start()
        self.addCleanup(environment.stop)
        def test_owner(x_test_user: str = Header(default="alice")) -> str:
            return x_test_user
        app.dependency_overrides[require_owner] = test_owner
        self.addCleanup(app.dependency_overrides.clear)
        self.client = TestClient(app)

    def test_users_are_isolated(self):
        created = self.client.post("/api/expenses", json={"amount": "5", "category": "Food"}).json()
        self.client.put("/api/budgets", json={"month": "2026-11", "category": "Food", "amount": "100"})
        bob = {"X-Test-User": "bob"}
        self.client.put("/api/budgets", headers=bob, json={"month": "2026-11", "category": "Food", "amount": "50"})
        self.assertEqual(self.client.get("/api/expenses", headers=bob).json(), [])
        self.assertEqual(self.client.delete(f"/api/expenses/{created['id']}", headers=bob).status_code, 404)
        self.assertEqual(self.client.put(f"/api/expenses/{created['id']}", headers=bob, json={
            "amount": "1", "category": "Food", "expense_date": "2026-11-01"
        }).status_code, 404)
        self.assertEqual(self.client.get("/api/summary?month=2026-11", headers=bob).json()["categories"][0]["budget"], "50.00")
        self.assertEqual(self.client.get("/api/summary?month=2026-11").json()["categories"][0]["budget"], "100.00")

    def test_expense_and_budget_workflow(self):
        budget = self.client.put("/api/budgets", json={"month": "2026-11", "category": "Food", "amount": "1000.00"})
        self.assertEqual(budget.status_code, 200)
        self.assertEqual(budget.json(), {"month": "2026-11", "category": "food", "amount": "1000.00"})
        expense = self.client.post("/api/expenses", json={"amount": "150.50", "category": "Food", "expense_date": "2026-11-18", "description": "Lunch"})
        self.assertEqual(expense.status_code, 201)
        expense_id = expense.json()["id"]
        self.assertEqual(expense.json(), {"id": expense_id, "date": "2026-11-18", "category": "food", "amount": "150.50", "description": "Lunch"})
        self.assertEqual(self.client.get("/api/expenses", params={"month": "2026-11", "category": "FOOD"}).json(), [expense.json()])
        summary = self.client.get("/api/summary", params={"month": "2026-11"}).json()
        self.assertEqual(summary, {"month": "2026-11", "total_spent": "150.50", "categories": [{"category": "food", "spent": "150.50", "budget": "1000.00", "remaining": "849.50", "over_budget": False}]})
        deleted = self.client.delete(f"/api/expenses/{expense_id}")
        self.assertEqual(deleted.status_code, 200)
        self.assertEqual(deleted.json(), {"id": expense_id, "deleted": True})
        self.assertEqual(self.client.delete(f"/api/expenses/{expense_id}").status_code, 404)

    def test_openapi_documents_all_operations(self):
        paths = self.client.get("/openapi.json").json()["paths"]
        operations = [(path, method, operation) for path, methods in paths.items() for method, operation in methods.items()]
        self.assertEqual(len(operations), 6)
        for path, method, operation in operations:
            with self.subTest(path=path, method=method):
                self.assertTrue(operation.get("description"))

    def test_invalid_inputs(self):
        self.assertEqual(self.client.get("/api/summary", params={"month": "invalid"}).status_code, 400)
        response = self.client.post("/api/expenses", json={"amount": "0", "category": "Food"})
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()["detail"][0]["loc"], ["body", "amount"])
        self.assertEqual(self.client.post("/api/expenses", json={"amount": "1.00", "category": "Food", "expense_date": "2026-02-30"}).status_code, 422)
        self.assertEqual(self.client.put("/api/budgets", json={"amount": "10", "category": " ", "month": "bad"}).status_code, 422)

    def test_edit_expense_moves_it_between_months(self):
        created = self.client.post("/api/expenses", json={"amount": "12.34", "category": "Food", "expense_date": "2026-10-01"}).json()
        expense_id = created["id"]
        response = self.client.put(f"/api/expenses/{expense_id}", json={
            "amount": "45.67", "category": " Travel ", "expense_date": "2026-11-02", "description": " Train "
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"id": expense_id, "date": "2026-11-02", "category": "travel", "amount": "45.67", "description": "Train"})
        self.assertEqual(self.client.get("/api/expenses", params={"month": "2026-10"}).json(), [])
        self.assertEqual(self.client.get("/api/expenses", params={"month": "2026-11"}).json(), [response.json()])
        self.assertEqual(self.client.get("/api/summary", params={"month": "2026-10"}).json()["total_spent"], "0.00")
        self.assertEqual(self.client.get("/api/summary", params={"month": "2026-11"}).json()["total_spent"], "45.67")

    def test_edit_expense_rejects_invalid_and_missing_values(self):
        original = self.client.post("/api/expenses", json={"amount": "12.34", "category": "Food", "expense_date": "2026-10-01"}).json()
        expense_id = original["id"]
        for data in (
            {"amount": "0", "category": "Food", "expense_date": "2026-10-01"},
            {"amount": "12.34", "category": " ", "expense_date": "2026-10-01"},
            {"amount": "12.34", "category": "Food", "expense_date": ""},
            {"amount": "12.34", "category": "Food", "expense_date": "2026-02-30"},
            {"amount": "12.34", "category": "Food"},
        ):
            with self.subTest(data=data):
                self.assertEqual(self.client.put(f"/api/expenses/{expense_id}", json=data).status_code, 422)
        self.assertEqual(self.client.get("/api/expenses").json(), [original])
        self.assertEqual(self.client.put("/api/expenses/99999", json={"amount": "1.00", "category": "Food", "expense_date": "2026-10-01"}).status_code, 404)


if __name__ == "__main__":
    unittest.main()