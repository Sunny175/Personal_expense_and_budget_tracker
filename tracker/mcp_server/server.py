from fastmcp import FastMCP

from tracker.core import tracker


mcp = FastMCP("Personal Expense and Budget Tracker")

mcp.tool()(tracker.add_expense)
mcp.tool()(tracker.list_expenses)
mcp.tool()(tracker.delete_expense)
mcp.tool()(tracker.set_budget)
mcp.tool()(tracker.monthly_summary)


if __name__ == "__main__":
    mcp.run(transport="stdio")
