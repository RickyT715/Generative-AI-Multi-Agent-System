"""Tests for supervisor/router query classification."""

import pytest


class TestRouteQuery:
    """Test the RouteQuery model."""

    def test_route_query_sql(self):
        from src.agents.supervisor import RouteQuery

        route = RouteQuery(datasource="sql_agent")
        assert route.datasource == "sql_agent"

    def test_route_query_rag(self):
        from src.agents.supervisor import RouteQuery

        route = RouteQuery(datasource="rag_agent")
        assert route.datasource == "rag_agent"

    def test_route_query_general(self):
        from src.agents.supervisor import RouteQuery

        route = RouteQuery(datasource="general")
        assert route.datasource == "general"

    def test_route_query_invalid(self):
        from src.agents.supervisor import RouteQuery

        with pytest.raises(ValueError):
            RouteQuery(datasource="invalid_agent")


class TestRouteFunction:
    """Test the route_question function."""

    def test_route_to_sql_agent(self):
        from src.graph import route_question

        state = {"query_category": "sql_agent"}
        assert route_question(state) == "sql_agent"

    def test_route_to_rag_agent(self):
        from src.graph import route_question

        state = {"query_category": "rag_agent"}
        assert route_question(state) == "rag_agent"

    def test_route_to_general(self):
        from src.graph import route_question

        state = {"query_category": "general"}
        assert route_question(state) == "general_agent"

    def test_route_default_general(self):
        from src.graph import route_question

        state = {}
        assert route_question(state) == "general_agent"
