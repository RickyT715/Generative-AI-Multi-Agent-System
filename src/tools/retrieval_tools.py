"""Retrieval tools for RAG agent."""

from langchain_core.tools import tool

from src.db.vector_store import get_retriever


def get_retrieval_tools():
    """Get the retrieval tool for the RAG agent."""
    retriever = get_retriever()

    @tool(response_format="content_and_artifact")
    def retrieve_policy_documents(query: str):
        """Search and retrieve information from company policy documents.

        Use this tool to find information about refund policies, privacy policies,
        terms of service, and other company documentation.

        Args:
            query: The search query describing what policy information to find.
        """
        docs = retriever.invoke(query)
        if not docs:
            return "No relevant policy documents found.", []

        content_parts = []
        for i, doc in enumerate(docs, 1):
            source = doc.metadata.get("source", "Unknown")
            page = doc.metadata.get("page", "N/A")
            content_parts.append(
                f"[Source {i}: {source}, Page {page}]\n{doc.page_content}"
            )

        content = "\n\n---\n\n".join(content_parts)
        return content, docs

    return [retrieve_policy_documents]
