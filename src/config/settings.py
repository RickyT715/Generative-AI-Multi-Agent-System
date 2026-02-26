import os

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model

load_dotenv()

DEFAULT_MODELS = {
    "anthropic": "claude-sonnet-4-5-20250929",
    "openai": "gpt-4o",
    "google": "gemini-2.5-flash",
}


def get_llm(provider=None, model=None, temperature=None, **kwargs):
    """Create an LLM instance using init_chat_model factory.

    Supports switching providers via .env or function arguments.
    """
    provider = provider or os.getenv("LLM_PROVIDER", "anthropic")
    model = model or os.getenv("LLM_MODEL", DEFAULT_MODELS.get(provider, "gpt-4o"))
    temperature = (
        temperature
        if temperature is not None
        else float(os.getenv("LLM_TEMPERATURE", "0.0"))
    )

    model_string = f"{provider}:{model}" if ":" not in model else model
    return init_chat_model(model_string, temperature=temperature, **kwargs)


def get_embedding_model():
    """Get the HuggingFace embedding model for vector store operations."""
    from langchain_huggingface import HuggingFaceEmbeddings

    model_name = os.getenv(
        "EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
    )
    return HuggingFaceEmbeddings(model_name=model_name)


def get_sqlite_path():
    """Get the SQLite database path from environment."""
    return os.getenv("SQLITE_DB_PATH", "data/customer_support.db")


def get_chroma_settings():
    """Get ChromaDB configuration from environment."""
    return {
        "persist_directory": os.getenv("CHROMA_PERSIST_DIR", "data/chroma"),
        "collection_name": os.getenv(
            "CHROMA_COLLECTION_NAME", "policy_documents"
        ),
    }
