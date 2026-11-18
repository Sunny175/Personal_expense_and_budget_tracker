# Personal Expense and Budget Tracker MCP Server

A local Python MCP server that lets an MCP client record expenses and compare
spending with monthly category budgets. It uses the standalone FastMCP 2.x
package and stores data in SQLite.

## Set up with UV

Prerequisites: [UV](https://docs.astral.sh/uv/getting-started/installation/)
and Python 3.12 or newer. In PowerShell, from the project directory:

```powershell
uv sync
uv run python -m unittest discover -s tests -v
```

`uv sync` creates and manages `.venv` and installs the dependencies recorded in
`uv.lock`. This project was initialized with `uv init .`. To add FastMCP 2.x
to a project, use `uv add "fastmcp>=2,<3"`. You do not need to activate the environment
when using `uv run`. To add another dependency later, use `uv add package-name`.
Keep `pyproject.toml` and `uv.lock` in version control, but not `.venv`.

## Web application

The React frontend lives in `frontend/` and talks only to the FastAPI HTTP
endpoints. FastAPI and the MCP server use the same local SQLite database. Request
bodies are validated with Pydantic before the existing tracker operations run.
Node.js 20.19+ or 22.12+ is required for the frontend.

Run the API from the project directory:

```powershell
uv sync
uv run uvicorn api:app --host 127.0.0.1 --port 8000
```

In a second terminal, start the frontend:

```powershell
npm --prefix frontend install
npm --prefix frontend run dev
```

Open the URL printed by Vite (normally `http://localhost:5173`). During
development Vite forwards `/api` requests to `http://127.0.0.1:8000`.
The API documentation is available at `http://127.0.0.1:8000/docs`. This is a
local app without authentication; do not expose the API publicly.

To start the server directly, run `uv run python main.py`. It communicates over
standard input/output and waits for an MCP client, so it is not a web page.
Stop it with Ctrl+C. Normally, configure the client to start it for you instead.

## Connect in VS Code

Create `.vscode/mcp.json` in this project with the configuration below. Change
the directory if the project moves, and make sure `uv` is on VS Code's PATH.

```json
{
	"servers": {
		"expense-tracker": {
			"type": "stdio",
			"command": "uv",
			"args": [
				"--directory",
				"C:\\Users\\Sunny\\MCP_Projects\\Personal_expense_and_budget_tracker",
				"run",
				"python",
				"main.py"
			]
		}
	}
}
```

Start the server from VS Code's MCP server controls and enable its tools in your
MCP-capable chat. For example, ask: "Set my food budget for November 2026 to
200.00, record a 12.50 food expense on 2026-11-17, and show my monthly summary."
Review tool calls before allowing changes or deletion.

## Available tools

- `add_expense(amount, category, expense_date, description)` records an expense.
	`amount` is a string such as `"12.50"`; the date defaults to today.
- `list_expenses(month, category)` lists expenses, optionally filtered by month
	(`YYYY-MM`) and/or category.
- `delete_expense(expense_id)` removes an expense by ID and reports whether it existed.
- `set_budget(month, category, amount)` creates or replaces a monthly category budget.
- `monthly_summary(month)` shows total spending, category budgets, remaining
	amounts, and whether a category is over budget. Negative remaining means overspent.

Dates use `YYYY-MM-DD`; months use `YYYY-MM`. Amounts must be positive with at
most two decimal places. Categories are trimmed and normalized to lowercase
using Unicode case folding. All amounts are assumed to use the same currency;
the server does not convert or track currencies.

## Storage and design

By default, the database is stored at `~/.expense-tracker/expenses.db`. Set
`EXPENSE_TRACKER_DB` to an absolute file path in the MCP server configuration's
`env` object to use a different location. The server creates the directory and
tables as needed. Back up this file to preserve your records; it is not encrypted.
Only connect trusted MCP clients: they can read, add, and delete your financial data.

SQLite needs no separate database service and persists data across server runs.
Amounts are converted from decimal strings to integer cents so calculations do
not have floating-point rounding errors. FastMCP exposes the Python functions
as discoverable MCP tools. The direct dependency is restricted to FastMCP 2.x;
its required MCP protocol SDK is installed automatically as a dependency.
Tests use a temporary database and include a real stdio MCP client/server round trip.
