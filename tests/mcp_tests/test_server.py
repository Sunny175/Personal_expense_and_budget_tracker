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

    def test_standalone_mcp_module(self):
        async def run_client():
            server = StdioServerParameters(
                command=sys.executable,
                args=["-m", "tracker.mcp_server.server"],
                env={**os.environ, "EXPENSE_TRACKER_DB": self.db_path},
            )
            async with stdio_client(server) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    tools = await session.list_tools()
                    self.assertEqual({tool.name for tool in tools.tools},
                                     {"add_expense", "list_expenses", "delete_expense", "set_budget", "monthly_summary"})
                    result = await session.call_tool("add_expense", {"amount": "5.00", "category": "food", "expense_date": "2026-11-01"})
                    self.assertFalse(result.isError, result.content)
                    self.assertEqual(main.monthly_summary("2026-11")["total_spent"], "5.00")

        asyncio.run(run_client())


if __name__ == "__main__":
    unittest.main()