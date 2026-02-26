"""SQL agent for querying customer support database."""

from langchain.agents import create_agent

from src.prompts.sql_agent import SQL_AGENT_PROMPT
from src.tools.sql_tools import get_sql_tools


def create_sql_agent_graph(llm, db=None):
    """Create the SQL agent as a compiled graph.

    Args:
        llm: The language model to use.
        db: Optional SQLDatabase instance. Defaults to configured database.

    Returns:
        Compiled agent graph.
    """
    tools = get_sql_tools(llm, db)

    return create_agent(
        llm,
        tools=tools,
        system_prompt=SQL_AGENT_PROMPT,
        name="sql_agent",
    )
