"""Tests for configuration module."""

import os


class TestSettings:
    """Test settings and configuration."""

    def test_get_sqlite_path_default(self):
        from src.config.settings import get_sqlite_path

        # Remove env var to test default
        old = os.environ.pop("SQLITE_DB_PATH", None)
        try:
            path = get_sqlite_path()
            assert path == "data/customer_support.db"
        finally:
            if old is not None:
                os.environ["SQLITE_DB_PATH"] = old

    def test_get_sqlite_path_custom(self):
        from src.config.settings import get_sqlite_path

        os.environ["SQLITE_DB_PATH"] = "custom/path.db"
        try:
            assert get_sqlite_path() == "custom/path.db"
        finally:
            os.environ["SQLITE_DB_PATH"] = "data/customer_support.db"

    def test_get_chroma_settings_default(self):
        from src.config.settings import get_chroma_settings

        settings = get_chroma_settings()
        assert "persist_directory" in settings
        assert "collection_name" in settings
        assert isinstance(settings["persist_directory"], str)
        assert isinstance(settings["collection_name"], str)

    def test_default_models_dict(self):
        from src.config.settings import DEFAULT_MODELS

        assert "anthropic" in DEFAULT_MODELS
        assert "openai" in DEFAULT_MODELS
        assert "google" in DEFAULT_MODELS
