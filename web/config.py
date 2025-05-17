"""
Configuration module.

This module provides functionality for configuring the web application.
"""

import os
from typing import Any, Dict


class Config:
    """
    Configuration for the web application.

    Features:
    - Environment variable loading
    - Default configuration values
    - Application configuration
    """

    @staticmethod
    def get_app_config() -> Dict[str, Any]:
        """
        Get application configuration from environment variables with sensible defaults.

        Returns:
            Dictionary with application configuration
        """
        return {
            "host": os.environ.get("FLASK_HOST", "0.0.0.0"),
            "port": int(os.environ.get("FLASK_PORT", 5000)),
            "debug": os.environ.get("FLASK_DEBUG", "True").lower()
            in ("true", "1", "t"),
            "threaded": True,
        }

    @staticmethod
    def configure_flask_app(app):
        """
        Configure Flask application settings.

        Args:
            app: Flask application instance
        """
        # Session configuration
        app.config["SESSION_TYPE"] = os.environ.get(
            "SESSION_TYPE", "filesystem")

        # Security settings
        app.config["SECRET_KEY"] = os.environ.get(
            "SECRET_KEY", os.urandom(24).hex())

        # Other settings
        app.config["JSON_SORT_KEYS"] = False
        app.config["TEMPLATES_AUTO_RELOAD"] = True
