"""Unit tests for application configuration."""

import os
from unittest.mock import patch


class TestSettings:
    def test_settings_load_from_env(self):
        """Settings should load correctly from environment."""
        with patch.dict(
            os.environ,
            {
                "GROQ_API_KEY": "test-key-123",
                "APP_ENV": "test",
                "DEBUG": "false",
            },
        ):
            from app.core.config import Settings

            settings = Settings()
            assert settings.groq_api_key == "test-key-123"
            assert settings.app_env == "test"
            assert settings.debug is False

    def test_is_production_property(self):
        """is_production should return True only for production env."""
        with patch.dict(
            os.environ,
            {
                "GROQ_API_KEY": "test-key",
                "APP_ENV": "production",
            },
        ):
            from app.core.config import Settings

            settings = Settings()
            assert settings.is_production is True

    def test_is_not_production_in_development(self):
        with patch.dict(
            os.environ,
            {
                "GROQ_API_KEY": "test-key",
                "APP_ENV": "development",
            },
        ):
            from app.core.config import Settings

            settings = Settings()
            assert settings.is_production is False
