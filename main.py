"""Compatibility entry point for the standalone MCP server and tracker functions."""

from tracker.core.tracker import (
    add_expense,
    delete_expense,
    format_amount,
    list_expenses,
    monthly_summary,
    parse_amount,
    set_budget,
    update_expense,
    validate_category,
    validate_month,
)
from tracker.mcp_server.server import mcp
from tracker.storage.database import database


if __name__ == "__main__":
    mcp.run(transport="stdio")
