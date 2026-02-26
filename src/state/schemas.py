"""State schemas for the multi-agent system."""

from langgraph.graph import MessagesState


class CustomerSupportState(MessagesState):
    """State for the customer support multi-agent graph."""

    query_category: str  # "sql_agent" | "rag_agent" | "general"
    customer_id: str  # optional, extracted from query
