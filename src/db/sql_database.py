"""SQLite database connection for agent use."""

import os

from langchain_community.utilities import SQLDatabase

from src.config.settings import get_sqlite_path


def get_sql_database(db_path=None):
    """Get SQLDatabase instance for use with SQL agents."""
    db_path = db_path or get_sqlite_path()

    if not os.path.exists(db_path):
        raise FileNotFoundError(
            f"Database not found at {db_path}. Run 'python scripts/setup.py' first."
        )

    return SQLDatabase.from_uri(f"sqlite:///{db_path}")
