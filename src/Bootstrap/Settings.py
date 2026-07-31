from pydantic_settings import BaseSettings, SettingsConfigDict


class GmailConfig(BaseSettings):
    oauth_client_id: str = ""
    oauth_client_secret: str = ""
    scopes: list[str] = ["https://www.googleapis.com/auth/gmail.modify"]
    token_storage_path: str = "token.json"
    token_encryption_key: str = ""


class DatabaseConfig(BaseSettings):
    url: str = "sqlite+aiosqlite:///./gmail_mcp.db"
    driver: str = "aiosqlite"


class RailguardsConfig(BaseSettings):
    access_level: str = "owner"
    allowed_recipients: list[str] = []
    blocked_actions: list[str] = []
    rate_limits: dict[str, int] = {}


class MCPConfig(BaseSettings):
    server_name: str = "Gmail-MCP"
    host: str = "127.0.0.1"
    port: int = 8080


class LLMConfig(BaseSettings):
    provider: str = "openai"
    model: str = "gpt-4"
    api_key: str = ""


class NotificationsConfig(BaseSettings):
    webhook_url: str = ""
    redis_url: str = ""


class LoggingConfig(BaseSettings):
    level: str = "INFO"
    json_format: bool = True


class Settings(BaseSettings):
    gmail: GmailConfig = GmailConfig()
    database: DatabaseConfig = DatabaseConfig()
    railguards: RailguardsConfig = RailguardsConfig()
    mcp: MCPConfig = MCPConfig()
    llm: LLMConfig = LLMConfig()
    notifications: NotificationsConfig = NotificationsConfig()
    logging: LoggingConfig = LoggingConfig()

    model_config = SettingsConfigDict(
        env_prefix="GMAIL_MCP_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @classmethod
    def from_env(cls) -> "Settings":
        return cls()
