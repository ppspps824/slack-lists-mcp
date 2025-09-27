"""Configuration management using pydantic-settings."""

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings managed by pydantic-settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Slack configuration
    slack_bot_token: SecretStr = Field(
        ...,
        description="Slack Bot User OAuth Token",
        alias="SLACK_BOT_TOKEN",
    )

    # MCP Server configuration
    mcp_server_name: str = Field(
        default="Slack Lists MCP Server",
        description="Name of the MCP server",
        alias="MCP_SERVER_NAME",
    )

    mcp_server_version: str = Field(
        default="0.1.0",
        description="Version of the MCP server",
        alias="MCP_SERVER_VERSION",
    )

    # Logging configuration
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
        alias="LOG_LEVEL",
    )

    # Slack API configuration
    slack_api_timeout: int = Field(
        default=30,
        description="Timeout for Slack API calls in seconds",
        alias="SLACK_API_TIMEOUT",
    )

    slack_retry_count: int = Field(
        default=3,
        description="Number of retries for failed Slack API calls",
        alias="SLACK_RETRY_COUNT",
    )

    # Development settings
    debug_mode: bool = Field(
        default=False,
        description="Enable debug mode for detailed logging",
        alias="DEBUG_MODE",
    )

    @property
    def slack_bot_token_value(self) -> str:
        """Get the actual slack bot token value."""
        return self.slack_bot_token.get_secret_value()


# Singleton instance
_settings: Settings | None = None


def get_settings() -> Settings:
    """Get the singleton settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
