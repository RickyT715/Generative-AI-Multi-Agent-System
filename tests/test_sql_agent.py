"""Tests for SQL agent and tools."""

import pytest
from langchain_community.utilities import SQLDatabase


class TestSQLTools:
    """Test SQL database tools."""

    def test_get_sql_tools(self, fake_llm, temp_sqlite_db):
        from src.tools.sql_tools import get_sql_tools

        db = SQLDatabase.from_uri(f"sqlite:///{temp_sqlite_db}")
        tools = get_sql_tools(fake_llm, db=db)

        # Only sql_db_query is returned; schema is embedded in the prompt
        # and query_checker (hidden LLM call) is removed.
        assert len(tools) == 1
        assert tools[0].name == "sql_db_query"

    def test_get_db_schema(self, fake_llm, temp_sqlite_db):
        from src.tools.sql_tools import get_db_schema

        db = SQLDatabase.from_uri(f"sqlite:///{temp_sqlite_db}")
        schema = get_db_schema(db=db)

        assert "customers" in schema
        assert "products" in schema
        assert "tickets" in schema

    def test_query_tool(self, fake_llm, temp_sqlite_db):
        from src.tools.sql_tools import get_sql_tools

        db = SQLDatabase.from_uri(f"sqlite:///{temp_sqlite_db}")
        tools = get_sql_tools(fake_llm, db=db)

        query_tool = next(t for t in tools if t.name == "sql_db_query")
        result = query_tool.invoke("SELECT COUNT(*) FROM customers")

        assert "3" in result


class TestSQLDatabase:
    """Test SQL database connection."""

    def test_get_sql_database(self, temp_sqlite_db):
        from src.db.sql_database import get_sql_database

        db = get_sql_database(db_path=temp_sqlite_db)
        assert db is not None

    def test_get_sql_database_missing(self):
        from src.db.sql_database import get_sql_database

        with pytest.raises(FileNotFoundError):
            get_sql_database(db_path="nonexistent.db")
