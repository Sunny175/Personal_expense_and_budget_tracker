import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


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
