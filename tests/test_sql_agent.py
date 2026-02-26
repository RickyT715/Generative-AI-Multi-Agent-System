"""Tests for SQL agent and tools."""

import pytest
from langchain_community.utilities import SQLDatabase


class TestSQLTools:
    """Test SQL database tools."""

    def test_get_sql_tools(self, fake_llm, temp_sqlite_db):
        from src.tools.sql_tools import get_sql_tools

        db = SQLDatabase.from_uri(f"sqlite:///{temp_sqlite_db}")
        tools = get_sql_tools(fake_llm, db=db)

        assert len(tools) == 4
        tool_names = {t.name for t in tools}
        assert "sql_db_list_tables" in tool_names
        assert "sql_db_schema" in tool_names
        assert "sql_db_query" in tool_names
        assert "sql_db_query_checker" in tool_names

    def test_list_tables_tool(self, fake_llm, temp_sqlite_db):
        from src.tools.sql_tools import get_sql_tools

        db = SQLDatabase.from_uri(f"sqlite:///{temp_sqlite_db}")
        tools = get_sql_tools(fake_llm, db=db)

        list_tables = next(t for t in tools if t.name == "sql_db_list_tables")
        result = list_tables.invoke("")

        assert "customers" in result
        assert "products" in result
        assert "tickets" in result

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
