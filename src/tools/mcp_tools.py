"""MCP client setup for integrating MCP tools with LangGraph agents."""

import sys

from langchain_mcp_adapters.client import MultiServerMCPClient


def get_mcp_client():
    """Get a MultiServerMCPClient configured for the customer support MCP server."""
    return MultiServerMCPClient(
        {
            "customer_support": {
                "command": sys.executable,
                "args": ["src/mcp_servers/support_server.py"],
                "transport": "stdio",
            }
        }
    )


async def get_mcp_tools():
    """Get MCP tools from the customer support server.

    Returns a list of LangChain-compatible tools.
    Must be called within an async context.
    """
    async with get_mcp_client() as client:
        tools = client.get_tools()
        return tools
