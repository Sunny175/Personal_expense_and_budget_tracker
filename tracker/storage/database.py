import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


@contextmanager
def database() -> Iterator[sqlite3.Connection]:
    """Open the configured SQLite database, initialize its tables, and commit changes."""
    db_path = Path(
        os.environ.get("EXPENSE_TRACKER_DB", str(Path.home() / ".expense-tracker" / "authenticated.db"))
    ).expanduser()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path, timeout=10)
    connection.row_factory = sqlite3.Row
    try:
        with connection:
            connection.execute("BEGIN IMMEDIATE")
            version = connection.execute("PRAGMA user_version").fetchone()[0]
            tables = connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table' AND name IN ('expenses', 'budgets')"
            ).fetchall()
            if version == 0 and tables:
                raise RuntimeError(
                    "This database contains legacy unowned data. Use a separate authenticated database; "
                    "the existing database has not been migrated."
                )
            if version not in (0, 1):
                raise RuntimeError(f"Unsupported database schema version: {version}")
            connection.execute(
                """CREATE TABLE IF NOT EXISTS expenses (
                    id INTEGER PRIMARY KEY,
                    owner TEXT NOT NULL,
                    expense_date TEXT NOT NULL,
                    category TEXT NOT NULL COLLATE NOCASE,
                    amount_cents INTEGER NOT NULL,
                    description TEXT NOT NULL
                )"""
            )
            connection.execute(
                """CREATE TABLE IF NOT EXISTS budgets (
                    owner TEXT NOT NULL,
                    month TEXT NOT NULL,
                    category TEXT NOT NULL COLLATE NOCASE,
                    amount_cents INTEGER NOT NULL,
                    PRIMARY KEY (owner, month, category)
                )"""
            )
            connection.execute("PRAGMA user_version = 1")
            yield connection
    finally:
        connection.close()
