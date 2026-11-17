import asyncio
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import TextContent

import main


class TrackerTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.db_path = str(Path(self.temp_dir.name) / "expenses.db")
        environment = patch.dict(os.environ, {"EXPENSE_TRACKER_DB": self.db_path})
        environment.start()
        self.addCleanup(environment.stop)

    def test_expenses_budgets_and_deletion(self):
        main.set_budget("2026-11", "Food", "100.00")
        main.set_budget("2026-11", "FOOD", "50.00")
        expense = main.add_expense("12.34", "Food", "2026-11-01", "Lunch")
        main.add_expense("40.00", "FOOD", "2026-11-02")
        main.add_expense("10.00", "Travel", "2026-10-01")
        self.assertEqual(len(main.list_expenses("2026-11", "FOOD")), 2)
        summary = main.monthly_summary("2026-11")
        self.assertEqual(summary["total_spent"], "52.34")
        self.assertEqual(summary["categories"], [{"category": "food", "spent": "52.34", "budget": "50.00", "remaining": "-2.34", "over_budget": True}])
        self.assertTrue(main.delete_expense(expense["id"])["deleted"])
        self.assertFalse(main.delete_expense(expense["id"])["deleted"])
        self.assertEqual(main.monthly_summary("2026-11")["total_spent"], "40.00")

    def test_validation(self):
        for amount in ("0", "-1", "1.001", "NaN", "1e1000000", "abc"):
            with self.subTest(amount=amount), self.assertRaises(ValueError):
                main.add_expense(amount, "food")
        for month in ("2026-13", "2026-1", "0000-01"):
            with self.subTest(month=month), self.assertRaises(ValueError):
                main.monthly_summary(month)
        with self.assertRaises(ValueError):
            main.add_expense("1.00", "food", "2026-02-30")
        with self.assertRaises(ValueError):
            main.set_budget("2026-11", "   ", "5")

    def test_mcp_stdio_round_trip(self):
        async def run_client():
            server = StdioServerParameters(
                command=sys.executable,
                args=[str(Path(main.__file__).resolve())],
                env={**os.environ, "EXPENSE_TRACKER_DB": self.db_path},
            )
            async with stdio_client(server) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    tools = await session.list_tools()
                    self.assertEqual({tool.name for tool in tools.tools},
                                     {"add_expense", "list_expenses", "delete_expense", "set_budget", "monthly_summary"})
                    result = await session.call_tool("add_expense", {"amount": "3.25", "category": "food", "expense_date": "2026-11-01"})
                    self.assertFalse(result.isError, result.content)
                    summary = await session.call_tool("monthly_summary", {"month": "2026-11"})
                    self.assertFalse(summary.isError, summary.content)
                    self.assertIsInstance(summary.content[0], TextContent)
                    if isinstance(summary.content[0], TextContent):
                        self.assertEqual(json.loads(summary.content[0].text)["total_spent"], "3.25")

        asyncio.run(run_client())


if __name__ == "__main__":
    unittest.main()