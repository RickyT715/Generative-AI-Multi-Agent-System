"""Tests for the main graph assembly."""

from src.state.schemas import CustomerSupportState


class TestCustomerSupportState:
    """Test the state schema."""

    def test_state_has_required_fields(self):
        assert "query_category" in CustomerSupportState.__annotations__
        assert "customer_id" in CustomerSupportState.__annotations__


class TestGraphConstruction:
    """Test graph construction (without invoking — requires LLM)."""

    def test_route_question_function(self):
        from src.graph import route_question

        assert route_question({"query_category": "sql_agent"}) == "sql_agent"
        assert route_question({"query_category": "rag_agent"}) == "rag_agent"
        assert route_question({"query_category": "general"}) == "general_agent"

    def test_supervisor_prompt_exists(self):
        from src.prompts.supervisor import SUPERVISOR_PROMPT

        assert "sql_agent" in SUPERVISOR_PROMPT
        assert "rag_agent" in SUPERVISOR_PROMPT
        assert "general" in SUPERVISOR_PROMPT


class TestDataGeneration:
    """Test the synthetic data generation."""

    def test_generate_customers(self):
        from data.seed.generate_data import generate_customers

        customers = generate_customers(10)
        assert len(customers) == 10
        assert all("name" in c for c in customers)
        assert all("email" in c for c in customers)
        assert all("customer_id" in c for c in customers)

    def test_generate_products(self):
        from data.seed.generate_data import generate_products

        products = generate_products()
        assert len(products) == 15
        assert all("name" in p for p in products)
        assert all("price" in p for p in products)

    def test_generate_tickets(self):
        from data.seed.generate_data import (
            generate_customers,
            generate_products,
            generate_tickets,
        )

        customers = generate_customers(10)
        products = generate_products()
        tickets = generate_tickets(customers, products, 50)
        assert len(tickets) == 50
        assert all("ticket_id" in t for t in tickets)
        assert all("category" in t for t in tickets)

    def test_seed_database(self, temp_sqlite_db):
        """Test that the seed database creates proper tables."""
        import sqlite3

        conn = sqlite3.connect(temp_sqlite_db)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cursor.fetchall()}
        conn.close()

        assert "customers" in tables
        assert "products" in tables
        assert "tickets" in tables
