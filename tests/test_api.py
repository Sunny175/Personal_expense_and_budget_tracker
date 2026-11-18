import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from api import app


class ApiTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        environment = patch.dict(os.environ, {"EXPENSE_TRACKER_DB": str(Path(directory.name) / "test.db")})
        environment.start()
        self.addCleanup(environment.stop)
        self.client = TestClient(app)

    def test_expense_and_budget_workflow(self):
        budget = self.client.put("/api/budgets", json={"month": "2026-11", "category": "Food", "amount": "100.00"})
        self.assertEqual(budget.status_code, 200)
        expense = self.client.post("/api/expenses", json={"amount": "12.50", "category": "Food", "expense_date": "2026-11-18", "description": "Lunch"})
        self.assertEqual(expense.status_code, 201)
        self.assertEqual(len(self.client.get("/api/expenses", params={"month": "2026-11"}).json()), 1)
        summary = self.client.get("/api/summary", params={"month": "2026-11"}).json()
        self.assertEqual(summary["total_spent"], "12.50")
        self.assertEqual(summary["categories"][0]["remaining"], "87.50")
        expense_id = expense.json()["id"]
        self.assertEqual(self.client.delete(f"/api/expenses/{expense_id}").status_code, 200)
        self.assertEqual(self.client.delete(f"/api/expenses/{expense_id}").status_code, 404)

    def test_invalid_inputs(self):
        self.assertEqual(self.client.get("/api/summary", params={"month": "invalid"}).status_code, 400)
        response = self.client.post("/api/expenses", json={"amount": "0", "category": "Food"})
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()["detail"][0]["loc"], ["body", "amount"])
        self.assertEqual(self.client.post("/api/expenses", json={"amount": "1.00", "category": "Food", "expense_date": "2026-02-30"}).status_code, 422)
        self.assertEqual(self.client.put("/api/budgets", json={"amount": "10", "category": " ", "month": "bad"}).status_code, 422)


if __name__ == "__main__":
    unittest.main()