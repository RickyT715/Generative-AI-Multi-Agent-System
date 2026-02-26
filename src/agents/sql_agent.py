"""SQL agent for querying customer support database."""

from langchain.agents import create_agent

from src.prompts.sql_agent import get_sql_agent_prompt
from src.tools.sql_tools import get_db_schema, get_sql_tools


def create_sql_agent_graph(llm, db=None):
    """Create the SQL agent as a compiled graph.

    Args:
        llm: The language model to use.
        db: Optional SQLDatabase instance. Defaults to configured database.

    Returns:
        Compiled agent graph.
    """
    tools = get_sql_tools(llm, db)
    schema = get_db_schema(db)
    prompt = get_sql_agent_prompt(schema)

    return create_agent(
        llm,
        tools=tools,
        system_prompt=prompt,
        name="sql_agent",
    )
