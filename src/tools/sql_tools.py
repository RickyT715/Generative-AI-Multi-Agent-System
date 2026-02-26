"""SQL database tools using SQLDatabaseToolkit."""

from langchain_community.agent_toolkits import SQLDatabaseToolkit

from src.db.sql_database import get_sql_database


def get_sql_tools(llm, db=None):
    """Get SQL database tools for the SQL agent.

    Returns the 4 standard SQL tools:
    - sql_db_list_tables
    - sql_db_schema
    - sql_db_query_checker
    - sql_db_query
    """
    db = db or get_sql_database()
    toolkit = SQLDatabaseToolkit(db=db, llm=llm)
    return toolkit.get_tools()
