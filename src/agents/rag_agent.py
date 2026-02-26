"""RAG agent for querying company policy documents."""

from langchain.agents import create_agent

from src.prompts.rag_agent import RAG_AGENT_PROMPT
from src.tools.retrieval_tools import get_retrieval_tools


def create_rag_agent_graph(llm):
    """Create the RAG agent as a compiled graph.

    Args:
        llm: The language model to use.

    Returns:
        Compiled agent graph.
    """
    tools = get_retrieval_tools()

    return create_agent(
        llm,
        tools=tools,
        system_prompt=RAG_AGENT_PROMPT,
        name="rag_agent",
    )
