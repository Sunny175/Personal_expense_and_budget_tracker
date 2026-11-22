import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tracker.core import tracker


class TrackerTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        environment = patch.dict(os.environ, {"EXPENSE_TRACKER_DB": str(Path(directory.name) / "expenses.db")})
        environment.start()
        self.addCleanup(environment.stop)

    def test_expenses_budgets_and_deletion(self):
        tracker.set_budget("2026-11", "Food", "100.00")
        tracker.set_budget("2026-11", "FOOD", "50.00")
        expense = tracker.add_expense("12.34", "Food", "2026-11-01", "Lunch")
        tracker.add_expense("40.00", "FOOD", "2026-11-02")
        tracker.add_expense("10.00", "Travel", "2026-10-01")
        self.assertEqual(len(tracker.list_expenses("2026-11", "FOOD")), 2)
        summary = tracker.monthly_summary("2026-11")
        self.assertEqual(summary["total_spent"], "52.34")
        self.assertEqual(summary["categories"], [{"category": "food", "spent": "52.34", "budget": "50.00", "remaining": "-2.34", "over_budget": True}])
        self.assertTrue(tracker.delete_expense(expense["id"])["deleted"])
        self.assertFalse(tracker.delete_expense(expense["id"])["deleted"])
        self.assertEqual(tracker.monthly_summary("2026-11")["total_spent"], "40.00")

    def test_validation(self):
        for amount in ("0", "-1", "1.001", "NaN", "1e1000000", "abc"):
            with self.subTest(amount=amount), self.assertRaises(ValueError):
                tracker.add_expense(amount, "food")
        for month in ("2026-13", "2026-1", "0000-01"):
            with self.subTest(month=month), self.assertRaises(ValueError):
                tracker.monthly_summary(month)
        with self.assertRaises(ValueError):
            tracker.add_expense("1.00", "food", "2026-02-30")
        with self.assertRaises(ValueError):
            tracker.set_budget("2026-11", "   ", "5")


if __name__ == "__main__":
    unittest.main()
