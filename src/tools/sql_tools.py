"""SQL database tools using SQLDatabaseToolkit."""

from langchain_community.agent_toolkits import SQLDatabaseToolkit

from src.db.sql_database import get_sql_database


def get_sql_tools(llm, db=None):
    """Get SQL database tools for the SQL agent.

    Returns only the query execution tool. Schema discovery (list_tables,
    schema) is handled by embedding schema in the system prompt, and the
    query_checker is removed because it makes a hidden LLM call.
    """
    db = db or get_sql_database()
    toolkit = SQLDatabaseToolkit(db=db, llm=llm)
    # Only keep sql_db_query — the other tools are either embedded in the
    # prompt (list_tables, schema) or add a hidden LLM call (query_checker).
    return [t for t in toolkit.get_tools() if t.name == "sql_db_query"]


def get_db_schema(db=None):
    """Return the full schema string for embedding in agent prompts."""
    db = db or get_sql_database()
    return db.get_table_info()
