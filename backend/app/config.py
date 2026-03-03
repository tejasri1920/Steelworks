# app/config.py
#
# Application-wide settings, read from environment variables (or a .env file).
#
# Pydantic's BaseSettings class automatically:
#   1. Reads variables from the process environment
#   2. Falls back to a .env file (if present)
#   3. Validates types (e.g., ensures DATABASE_URL is a string)
#   4. Raises a clear error on startup if required variables are missing
#
# This single source of truth prevents "works on my machine" mismatches
# and ensures the app fails fast if misconfigured — instead of silently
# using wrong values.

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Typed container for all environment-driven configuration.

    Attributes:
        DATABASE_URL: Full SQLAlchemy connection URL for PostgreSQL.
                      Example: postgresql://user:pass@host:5432/dbname
        ALLOWED_ORIGINS: Comma-separated list of origins allowed by CORS.
                         The frontend URL must be included here.
        LOG_LEVEL: uvicorn log verbosity (debug | info | warning | error).
        TESTING: Set to "true" in test environments to switch to SQLite.
    """

    # Required — no default means the app will refuse to start without it
    DATABASE_URL: str

    # Default covers local dev with the Vite dev server on :5173 and
    # the Docker Compose frontend on :3000
    ALLOWED_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    LOG_LEVEL: str = "info"

    # Used by the test suite to signal SQLite usage
    TESTING: str = "false"

    # model_config tells pydantic-settings where to find the .env file.
    # env_file_encoding handles Windows-style UTF-8 BOM characters.
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,    # DATABASE_URL and database_url both work
    )

    @property
    def allowed_origins_list(self) -> list[str]:
        """
        Converts the comma-separated ALLOWED_ORIGINS string to a Python list.

        Example:
            "http://localhost:5173,http://localhost:3000"
            → ["http://localhost:5173", "http://localhost:3000"]

        Time complexity: O(n) where n = number of origin strings.
        """
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]

    @property
    def is_testing(self) -> bool:
        """Returns True when running the test suite (TESTING=true)."""
        return self.TESTING.lower() == "true"


# Module-level singleton — imported by other modules with `from app.config import settings`
# This avoids re-reading the environment on every import.
settings = Settings()
