"""Main graph assembly — wires supervisor router with specialist agents."""

from langchain_core.messages import AIMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph

from src.agents.general_agent import create_general_agent_graph
from src.agents.rag_agent import create_rag_agent_graph
from src.agents.sql_agent import create_sql_agent_graph
from src.agents.supervisor import create_router
from src.config.settings import get_llm
from src.state.schemas import CustomerSupportState


def _make_agent_node(agent_graph):
    """Wrap a compiled agent graph into a node function for the supervisor graph.

    The agent graph uses its own internal state (messages-based).
    This wrapper invokes it and returns the final AI message.
    """

    def node_fn(state):
        result = agent_graph.invoke({"messages": state["messages"]})
        # Extract the last AI message from the agent's response
        agent_messages = result.get("messages", [])
        last_message = None
        for msg in reversed(agent_messages):
            if isinstance(msg, AIMessage):
                last_message = msg
                break

        if last_message is None and agent_messages:
            last_message = agent_messages[-1]

        if last_message is not None:
            return {"messages": [last_message]}
        return {
            "messages": [AIMessage(content="I was unable to process your request.")]
        }

    return node_fn


def route_question(state):
    """Route based on the query_category set by the supervisor."""
    category = state.get("query_category", "general")
    if category == "sql_agent":
        return "sql_agent"
    elif category == "rag_agent":
        return "rag_agent"
    else:
        return "general_agent"


def build_graph(llm=None, checkpointer=None):
    """Build the main multi-agent supervisor graph.

    Args:
        llm: Optional LLM instance. Defaults to configured LLM.
        checkpointer: Optional checkpointer for conversation persistence.

    Returns:
        Compiled StateGraph.
    """
    llm = llm or get_llm()

    # Create specialist agent graphs
    sql_agent = create_sql_agent_graph(llm)
    rag_agent = create_rag_agent_graph(llm)
    general_agent = create_general_agent_graph(llm)

    # Create the router
    router = create_router(llm)

    # Build the supervisor graph
    builder = StateGraph(CustomerSupportState)

    # Add nodes
    builder.add_node("router", router)
    builder.add_node("sql_agent", _make_agent_node(sql_agent))
    builder.add_node("rag_agent", _make_agent_node(rag_agent))
    builder.add_node("general_agent", _make_agent_node(general_agent))

    # Add edges
    builder.add_edge(START, "router")
    builder.add_conditional_edges(
        "router",
        route_question,
        {
            "sql_agent": "sql_agent",
            "rag_agent": "rag_agent",
            "general_agent": "general_agent",
        },
    )

    # All agents return to END
    builder.add_edge("sql_agent", END)
    builder.add_edge("rag_agent", END)
    builder.add_edge("general_agent", END)

    # Compile with checkpointer
    if checkpointer is None:
        checkpointer = InMemorySaver()

    return builder.compile(checkpointer=checkpointer)
