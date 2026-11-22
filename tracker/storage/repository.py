import sqlite3

from tracker.storage.database import database


def insert_expense(owner: str, expense_date: str, category: str, cents: int, description: str) -> int | None:
    with database() as connection:
        cursor = connection.execute(
            "INSERT INTO expenses (owner, expense_date, category, amount_cents, description) VALUES (?, ?, ?, ?, ?)",
            (owner, expense_date, category, cents, description),
        )
        return cursor.lastrowid


def get_expenses(owner: str, month: str, category: str) -> list[sqlite3.Row]:
    conditions = ["owner = ?"]
    parameters = [owner]
    if month:
        conditions.append("substr(expense_date, 1, 7) = ?")
        parameters.append(month)
    if category:
        conditions.append("category = ? COLLATE NOCASE")
        parameters.append(category)
    query = "SELECT id, expense_date, category, amount_cents, description FROM expenses"
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY expense_date DESC, id DESC"
    with database() as connection:
        return connection.execute(query, parameters).fetchall()


def remove_expense(owner: str, expense_id: int) -> bool:
    with database() as connection:
        return bool(connection.execute("DELETE FROM expenses WHERE owner = ? AND id = ?", (owner, expense_id)).rowcount)


def replace_expense(owner: str, expense_id: int, expense_date: str, category: str, cents: int, description: str) -> bool:
    with database() as connection:
        return bool(connection.execute(
            """UPDATE expenses SET expense_date = ?, category = ?, amount_cents = ?, description = ?
               WHERE owner = ? AND id = ?""",
            (expense_date, category, cents, description, owner, expense_id),
        ).rowcount)


def upsert_budget(owner: str, month: str, category: str, cents: int) -> None:
    with database() as connection:
        connection.execute(
            """INSERT INTO budgets (owner, month, category, amount_cents) VALUES (?, ?, ?, ?)
               ON CONFLICT(owner, month, category) DO UPDATE SET amount_cents = excluded.amount_cents""",
            (owner, month, category, cents),
        )


def get_monthly_totals(owner: str, month: str) -> tuple[list[sqlite3.Row], list[sqlite3.Row]]:
    with database() as connection:
        spending = connection.execute(
            """SELECT category, SUM(amount_cents) AS total FROM expenses
               WHERE owner = ? AND substr(expense_date, 1, 7) = ? GROUP BY category""", (owner, month)
        ).fetchall()
        budgets = connection.execute(
            "SELECT category, amount_cents FROM budgets WHERE owner = ? AND month = ?", (owner, month)
        ).fetchall()
    return spending, budgets
