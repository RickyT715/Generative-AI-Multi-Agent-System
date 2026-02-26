"""User scenario mock tests simulating end-to-end user interactions."""

from unittest.mock import MagicMock, patch

from langchain_core.messages import AIMessage, HumanMessage


class TestSupervisorRouting:
    """Test supervisor routing with mocked LLM."""

    def test_router_classifies_to_sql(self):
        """Mock LLM to return sql_agent classification."""
        from src.agents.supervisor import RouteQuery, create_router

        mock_llm = MagicMock()
        mock_structured = MagicMock()
        mock_llm.with_structured_output.return_value = mock_structured
        mock_structured.invoke.return_value = RouteQuery(datasource="sql_agent")

        router = create_router(mock_llm)
        state = {"messages": [HumanMessage(content="Show me John's tickets")]}
        result = router(state)

        assert result["query_category"] == "sql_agent"

    def test_router_classifies_to_rag(self):
        """Mock LLM to return rag_agent classification."""
        from src.agents.supervisor import RouteQuery, create_router

        mock_llm = MagicMock()
        mock_structured = MagicMock()
        mock_llm.with_structured_output.return_value = mock_structured
        mock_structured.invoke.return_value = RouteQuery(datasource="rag_agent")

        router = create_router(mock_llm)
        state = {"messages": [HumanMessage(content="What is the refund policy?")]}
        result = router(state)

        assert result["query_category"] == "rag_agent"

    def test_router_classifies_to_general(self):
        """Mock LLM to return general classification."""
        from src.agents.supervisor import RouteQuery, create_router

        mock_llm = MagicMock()
        mock_structured = MagicMock()
        mock_llm.with_structured_output.return_value = mock_structured
        mock_structured.invoke.return_value = RouteQuery(datasource="general")

        router = create_router(mock_llm)
        state = {"messages": [HumanMessage(content="Hello!")]}
        result = router(state)

        assert result["query_category"] == "general"

    def test_router_handles_empty_messages(self):
        """Router should default to general when no messages."""
        from src.agents.supervisor import create_router

        mock_llm = MagicMock()
        router = create_router(mock_llm)
        state = {"messages": []}
        result = router(state)

        assert result["query_category"] == "general"

    def test_router_handles_dict_messages(self):
        """Router should handle dict-format messages."""
        from src.agents.supervisor import RouteQuery, create_router

        mock_llm = MagicMock()
        mock_structured = MagicMock()
        mock_llm.with_structured_output.return_value = mock_structured
        mock_structured.invoke.return_value = RouteQuery(datasource="sql_agent")

        router = create_router(mock_llm)
        state = {"messages": [{"role": "user", "content": "How many customers?"}]}
        result = router(state)

        assert result["query_category"] == "sql_agent"


class TestAgentNodeWrapper:
    """Test the agent node wrapper function."""

    def test_make_agent_node_extracts_ai_message(self):
        from src.graph import _make_agent_node

        mock_agent = MagicMock()
        ai_msg = AIMessage(content="Here is the answer")
        mock_agent.invoke.return_value = {"messages": [ai_msg]}

        node_fn = _make_agent_node(mock_agent)
        result = node_fn({"messages": [HumanMessage(content="test")]})

        assert len(result["messages"]) == 1
        assert result["messages"][0].content == "Here is the answer"

    def test_make_agent_node_handles_no_ai_message(self):
        from src.graph import _make_agent_node

        mock_agent = MagicMock()
        human_msg = HumanMessage(content="test")
        mock_agent.invoke.return_value = {"messages": [human_msg]}

        node_fn = _make_agent_node(mock_agent)
        result = node_fn({"messages": [HumanMessage(content="test")]})

        assert len(result["messages"]) == 1

    def test_make_agent_node_handles_empty_messages(self):
        from src.graph import _make_agent_node

        mock_agent = MagicMock()
        mock_agent.invoke.return_value = {"messages": []}

        node_fn = _make_agent_node(mock_agent)
        result = node_fn({"messages": [HumanMessage(content="test")]})

        assert len(result["messages"]) == 1
        assert "unable to process" in result["messages"][0].content.lower()


class TestSQLToolExecution:
    """Test SQL tool execution with real database."""

    def test_schema_tool_returns_columns(self, fake_llm, temp_sqlite_db):
        from langchain_community.utilities import SQLDatabase

        from src.tools.sql_tools import get_sql_tools

        db = SQLDatabase.from_uri(f"sqlite:///{temp_sqlite_db}")
        tools = get_sql_tools(fake_llm, db=db)

        schema_tool = next(t for t in tools if t.name == "sql_db_schema")
        result = schema_tool.invoke("customers")

        assert "customer_id" in result
        assert "name" in result
        assert "email" in result

    def test_query_specific_customer(self, fake_llm, temp_sqlite_db):
        from langchain_community.utilities import SQLDatabase

        from src.tools.sql_tools import get_sql_tools

        db = SQLDatabase.from_uri(f"sqlite:///{temp_sqlite_db}")
        tools = get_sql_tools(fake_llm, db=db)

        query_tool = next(t for t in tools if t.name == "sql_db_query")
        result = query_tool.invoke(
            "SELECT name, email FROM customers WHERE name LIKE '%John%'"
        )

        assert "John Doe" in result
        assert "john@example.com" in result

    def test_query_ticket_count_by_status(self, fake_llm, temp_sqlite_db):
        from langchain_community.utilities import SQLDatabase

        from src.tools.sql_tools import get_sql_tools

        db = SQLDatabase.from_uri(f"sqlite:///{temp_sqlite_db}")
        tools = get_sql_tools(fake_llm, db=db)

        query_tool = next(t for t in tools if t.name == "sql_db_query")
        result = query_tool.invoke(
            "SELECT status, COUNT(*) FROM tickets GROUP BY status"
        )

        assert "open" in result or "resolved" in result or "closed" in result

    def test_query_join_customers_tickets(self, fake_llm, temp_sqlite_db):
        from langchain_community.utilities import SQLDatabase

        from src.tools.sql_tools import get_sql_tools

        db = SQLDatabase.from_uri(f"sqlite:///{temp_sqlite_db}")
        tools = get_sql_tools(fake_llm, db=db)

        query_tool = next(t for t in tools if t.name == "sql_db_query")
        result = query_tool.invoke(
            "SELECT c.name, t.subject FROM customers c "
            "JOIN tickets t ON c.customer_id = t.customer_id "
            "WHERE c.name = 'John Doe'"
        )

        assert "John Doe" in result
        assert "Billing Issue" in result


class TestPromptContent:
    """Test that all prompts contain expected content."""

    def test_sql_prompt_has_safety_rules(self):
        from src.prompts.sql_agent import SQL_AGENT_PROMPT

        assert "NEVER" in SQL_AGENT_PROMPT
        assert "INSERT" in SQL_AGENT_PROMPT or "DELETE" in SQL_AGENT_PROMPT

    def test_sql_prompt_has_table_names(self):
        from src.prompts.sql_agent import SQL_AGENT_PROMPT

        assert "customers" in SQL_AGENT_PROMPT
        assert "products" in SQL_AGENT_PROMPT
        assert "tickets" in SQL_AGENT_PROMPT

    def test_rag_prompt_has_tool_name(self):
        from src.prompts.rag_agent import RAG_AGENT_PROMPT

        assert "retrieve_policy_documents" in RAG_AGENT_PROMPT

    def test_supervisor_prompt_has_all_routes(self):
        from src.prompts.supervisor import SUPERVISOR_PROMPT

        assert "sql_agent" in SUPERVISOR_PROMPT
        assert "rag_agent" in SUPERVISOR_PROMPT
        assert "general" in SUPERVISOR_PROMPT

    def test_general_agent_prompt_exists(self):
        from src.agents.general_agent import GENERAL_AGENT_PROMPT

        assert "TechCorp" in GENERAL_AGENT_PROMPT
        assert len(GENERAL_AGENT_PROMPT) > 100


class TestGraphBuild:
    """Test graph construction with mocked agents."""

    def test_build_graph_returns_compiled(self):
        """Test that build_graph creates a valid compiled graph."""
        with (
            patch("src.graph.create_sql_agent_graph") as mock_sql,
            patch("src.graph.create_rag_agent_graph") as mock_rag,
            patch("src.graph.create_general_agent_graph") as mock_gen,
        ):
            mock_sql.return_value = MagicMock()
            mock_rag.return_value = MagicMock()
            mock_gen.return_value = MagicMock()

            mock_llm = MagicMock()
            mock_llm.with_structured_output.return_value = MagicMock()

            from src.graph import build_graph

            graph = build_graph(llm=mock_llm)
            assert graph is not None
            # Check that the graph has the expected nodes
            assert hasattr(graph, "invoke")
