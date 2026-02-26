"""Supervisor/router that classifies queries and routes to specialist agents."""

from typing import Literal

from langchain_core.messages import HumanMessage
from pydantic import BaseModel, Field

from src.prompts.supervisor import SUPERVISOR_PROMPT


class RouteQuery(BaseModel):
    """Route a user query to the appropriate specialist agent."""

    datasource: Literal["sql_agent", "rag_agent", "general"] = Field(
        description=(
            "Route to 'sql_agent' for customer data/tickets/product queries, "
            "'rag_agent' for policy/document questions, "
            "'general' for greetings and other general queries."
        )
    )


def create_router(llm):
    """Create a router that classifies queries using structured output.

    Args:
        llm: The language model to use for classification.

    Returns:
        A callable that takes a user message and returns a route decision.
    """
    structured_llm = llm.with_structured_output(RouteQuery)

    def route(state):
        """Classify the user's query and set the query_category in state."""
        messages = state.get("messages", [])

        # Get the latest user message
        user_message = None
        for msg in reversed(messages):
            if isinstance(msg, HumanMessage) or (
                isinstance(msg, dict) and msg.get("role") == "user"
            ):
                user_message = msg
                break

        if user_message is None:
            return {"query_category": "general"}

        content = (
            user_message.content
            if hasattr(user_message, "content")
            else user_message.get("content", "")
        )

        result = structured_llm.invoke(
            [
                {"role": "system", "content": SUPERVISOR_PROMPT},
                {"role": "user", "content": content},
            ]
        )

        return {"query_category": result.datasource}

    return route
