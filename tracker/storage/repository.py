import sqlite3

from tracker.storage.database import database


def insert_expense(expense_date: str, category: str, cents: int, description: str) -> int | None:
    with database() as connection:
        cursor = connection.execute(
            "INSERT INTO expenses (expense_date, category, amount_cents, description) VALUES (?, ?, ?, ?)",
            (expense_date, category, cents, description),
        )
        return cursor.lastrowid


def get_expenses(month: str, category: str) -> list[sqlite3.Row]:
    conditions = []
    parameters = []
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


def remove_expense(expense_id: int) -> bool:
    with database() as connection:
        return bool(connection.execute("DELETE FROM expenses WHERE id = ?", (expense_id,)).rowcount)


def replace_expense(expense_id: int, expense_date: str, category: str, cents: int, description: str) -> bool:
    with database() as connection:
        return bool(connection.execute(
            """UPDATE expenses SET expense_date = ?, category = ?, amount_cents = ?, description = ?
               WHERE id = ?""",
            (expense_date, category, cents, description, expense_id),
        ).rowcount)


def upsert_budget(month: str, category: str, cents: int) -> None:
    with database() as connection:
        connection.execute(
            """INSERT INTO budgets (month, category, amount_cents) VALUES (?, ?, ?)
               ON CONFLICT(month, category) DO UPDATE SET amount_cents = excluded.amount_cents""",
            (month, category, cents),
        )


def get_monthly_totals(month: str) -> tuple[list[sqlite3.Row], list[sqlite3.Row]]:
    with database() as connection:
        spending = connection.execute(
            """SELECT category, SUM(amount_cents) AS total FROM expenses
               WHERE substr(expense_date, 1, 7) = ? GROUP BY category""", (month,)
        ).fetchall()
        budgets = connection.execute(
            "SELECT category, amount_cents FROM budgets WHERE month = ?", (month,)
        ).fetchall()
    return spending, budgets
