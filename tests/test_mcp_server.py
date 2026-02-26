"""Tests for MCP server tools."""

import pytest


class TestMCPServerTools:
    """Test MCP server tool functions directly."""

    @pytest.fixture(autouse=True)
    def setup_db(self, temp_sqlite_db):
        """Set up the database path for MCP server tests."""
        import src.mcp_servers.support_server as server

        self._orig_db = server.DB_PATH
        server.DB_PATH = temp_sqlite_db
        yield
        server.DB_PATH = self._orig_db

    def test_lookup_customer_found(self):
        from src.mcp_servers.support_server import lookup_customer

        result = lookup_customer("John")
        assert "John Doe" in result
        assert "john@example.com" in result

    def test_lookup_customer_not_found(self):
        from src.mcp_servers.support_server import lookup_customer

        result = lookup_customer("Nonexistent Person")
        assert "No customer found" in result

    def test_lookup_customer_partial_match(self):
        from src.mcp_servers.support_server import lookup_customer

        result = lookup_customer("Jane")
        assert "Jane Smith" in result

    def test_get_ticket_history_found(self):
        from src.mcp_servers.support_server import get_ticket_history

        result = get_ticket_history(1)
        assert "Billing Issue" in result
        assert "Login Problem" in result

    def test_get_ticket_history_not_found(self):
        from src.mcp_servers.support_server import get_ticket_history

        result = get_ticket_history(999)
        assert "No tickets found" in result

    def test_create_ticket_success(self):
        from src.mcp_servers.support_server import create_ticket

        result = create_ticket(
            customer_id=1,
            subject="Test Ticket",
            description="Testing ticket creation",
            priority="high",
            category="technical",
        )
        assert "created successfully" in result
        assert "Test Ticket" in result

    def test_create_ticket_invalid_customer(self):
        from src.mcp_servers.support_server import create_ticket

        result = create_ticket(
            customer_id=999,
            subject="Test",
            description="Test",
        )
        assert "Error" in result
        assert "not found" in result


class TestMCPServerInstance:
    """Test MCP server configuration."""

    def test_mcp_server_exists(self):
        from src.mcp_servers.support_server import mcp

        assert mcp is not None
        assert mcp.name == "CustomerSupport"
