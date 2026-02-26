"""Tests for RAG agent and retrieval tools."""

import os
import tempfile

import pytest


class TestVectorStore:
    """Test vector store operations."""

    def test_get_chroma_settings(self):
        from src.config.settings import get_chroma_settings

        settings = get_chroma_settings()
        assert "persist_directory" in settings
        assert "collection_name" in settings

    @pytest.mark.integration
    def test_vector_store_creation(self):
        """Test that vector store can be created (requires embedding model)."""
        from src.db.vector_store import get_vector_store

        os.environ["CHROMA_PERSIST_DIR"] = tempfile.mkdtemp()
        store = get_vector_store()
        assert store is not None


class TestRAGPrompt:
    """Test RAG agent prompt configuration."""

    def test_rag_prompt_exists(self):
        from src.prompts.rag_agent import RAG_AGENT_PROMPT

        assert "retrieve_policy_documents" in RAG_AGENT_PROMPT
        assert "policy" in RAG_AGENT_PROMPT.lower()
