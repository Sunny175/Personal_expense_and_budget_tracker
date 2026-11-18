import os
import re
import sqlite3
from contextlib import contextmanager
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Iterator

from fastmcp import FastMCP


mcp = FastMCP("Personal Expense and Budget Tracker")


@contextmanager
def database() -> Iterator[sqlite3.Connection]:
    """Open the configured SQLite database, initialize its tables, and commit changes."""
    db_path = Path(
        os.environ.get("EXPENSE_TRACKER_DB", str(Path.home() / ".expense-tracker" / "expenses.db"))
    ).expanduser()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path, timeout=10)
    connection.row_factory = sqlite3.Row
    try:
        with connection:
            connection.execute(
                """CREATE TABLE IF NOT EXISTS expenses (
                    id INTEGER PRIMARY KEY,
                    expense_date TEXT NOT NULL,
                    category TEXT NOT NULL COLLATE NOCASE,
                    amount_cents INTEGER NOT NULL,
                    description TEXT NOT NULL
                )"""
            )
            connection.execute(
                """CREATE TABLE IF NOT EXISTS budgets (
                    month TEXT NOT NULL,
                    category TEXT NOT NULL COLLATE NOCASE,
                    amount_cents INTEGER NOT NULL,
                    PRIMARY KEY (month, category)
                )"""
            )
            yield connection
    finally:
        connection.close()


def parse_amount(amount: str) -> int:
    """Validate a positive decimal amount and return it in integer cents."""
    try:
        value = Decimal(amount)
        exponent = value.as_tuple().exponent
        if (
            not value.is_finite()
            or not isinstance(exponent, int)
            or value <= 0
            or value > 90_000_000_000_000
            or exponent < -2
        ):
            raise ValueError
        cents = value * 100
        return int(cents)
    except (InvalidOperation, ValueError):
        raise ValueError("Amount must be positive with at most two decimal places.") from None


def format_amount(cents: int) -> str:
    """Format signed integer cents as a two-decimal amount string."""
    sign = "-" if cents < 0 else ""
    cents = abs(cents)
    return f"{sign}{cents // 100}.{cents % 100:02d}"


def validate_month(month: str) -> str:
    """Return a valid YYYY-MM month or raise ValueError."""
    if not re.fullmatch(r"[0-9]{4}-(0[1-9]|1[0-2])", month) or month.startswith("0000-"):
        raise ValueError("Month must be in YYYY-MM format.")
    return month


def validate_category(category: str) -> str:
    """Trim and case-fold a nonempty category or raise ValueError."""
    category = category.strip()
    if not category:
        raise ValueError("Category cannot be empty.")
    return category.casefold()


def add_expense(amount: str, category: str, expense_date: str = "", description: str = "") -> dict:
    """Record an expense. Amount is a decimal string; date is YYYY-MM-DD (default: today)."""
    cents = parse_amount(amount)
    category = validate_category(category)
    if expense_date:
        try:
            parsed_date = date.fromisoformat(expense_date)
            if parsed_date.isoformat() != expense_date:
                raise ValueError
        except ValueError:
            raise ValueError("Expense date must be in YYYY-MM-DD format.") from None
    else:
        expense_date = date.today().isoformat()
    with database() as connection:
        cursor = connection.execute(
            "INSERT INTO expenses (expense_date, category, amount_cents, description) VALUES (?, ?, ?, ?)",
            (expense_date, category, cents, description.strip()),
        )
        return {"id": cursor.lastrowid, "date": expense_date, "category": category,
                "amount": format_amount(cents), "description": description.strip()}


def list_expenses(month: str = "", category: str = "") -> list[dict]:
    """List expenses, optionally filtered by YYYY-MM and category."""
    conditions = []
    parameters = []
    if month:
        conditions.append("substr(expense_date, 1, 7) = ?")
        parameters.append(validate_month(month))
    if category:
        conditions.append("category = ? COLLATE NOCASE")
        parameters.append(validate_category(category))
    query = "SELECT id, expense_date, category, amount_cents, description FROM expenses"
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY expense_date DESC, id DESC"
    with database() as connection:
        rows = connection.execute(query, parameters).fetchall()
    return [{"id": row["id"], "date": row["expense_date"], "category": row["category"],
             "amount": format_amount(row["amount_cents"]), "description": row["description"]}
            for row in rows]


def delete_expense(expense_id: int) -> dict:
    """Delete an expense by its ID."""
    with database() as connection:
        deleted = connection.execute("DELETE FROM expenses WHERE id = ?", (expense_id,)).rowcount
    return {"id": expense_id, "deleted": bool(deleted)}


def set_budget(month: str, category: str, amount: str) -> dict:
    """Set or replace a category budget for a month (YYYY-MM)."""
    month = validate_month(month)
    category = validate_category(category)
    cents = parse_amount(amount)
    with database() as connection:
        connection.execute(
            """INSERT INTO budgets (month, category, amount_cents) VALUES (?, ?, ?)
               ON CONFLICT(month, category) DO UPDATE SET amount_cents = excluded.amount_cents""",
            (month, category, cents),
        )
    return {"month": month, "category": category, "amount": format_amount(cents)}


def monthly_summary(month: str) -> dict:
    """Summarize spending and category budgets for a month (YYYY-MM)."""
    month = validate_month(month)
    with database() as connection:
        spending = connection.execute(
            """SELECT category, SUM(amount_cents) AS total FROM expenses
               WHERE substr(expense_date, 1, 7) = ? GROUP BY category""", (month,)
        ).fetchall()
        budgets = connection.execute(
            "SELECT category, amount_cents FROM budgets WHERE month = ?", (month,)
        ).fetchall()
    categories = {}
    for row in budgets:
        categories[row["category"].lower()] = {"category": row["category"], "budget": row["amount_cents"], "spent": 0}
    for row in spending:
        entry = categories.setdefault(row["category"].lower(), {"category": row["category"], "budget": None, "spent": 0})
        entry["spent"] = row["total"]
    result = []
    for entry in sorted(categories.values(), key=lambda item: item["category"].lower()):
        budget = entry["budget"]
        spent = entry["spent"]
        result.append({"category": entry["category"], "spent": format_amount(spent),
                       "budget": format_amount(budget) if budget is not None else None,
                       "remaining": format_amount(budget - spent) if budget is not None else None,
                       "over_budget": budget is not None and spent > budget})
    return {"month": month, "total_spent": format_amount(sum(row["total"] for row in spending)), "categories": result}


mcp.tool()(add_expense)
mcp.tool()(list_expenses)
mcp.tool()(delete_expense)
mcp.tool()(set_budget)
mcp.tool()(monthly_summary)


if __name__ == "__main__":
    mcp.run(transport="stdio")