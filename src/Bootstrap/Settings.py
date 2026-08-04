from pydantic_settings import BaseSettings, SettingsConfigDict


class GmailConfig(BaseSettings):
    oauth_client_id: str = ""
    oauth_client_secret: str = ""
    scopes: list[str] = ["https://www.googleapis.com/auth/gmail.modify"]
    token_storage_path: str = "token.json"
    token_encryption_key: str = ""


class DatabaseConfig(BaseSettings):
    # Synchronous driver: the repository ports and use cases (Phases 3-4) are
    # synchronous, so the persistence layer uses synchronous SQLAlchemy.
    url: str = "sqlite:///./gmail_mcp.db"
    driver: str = "sqlite"


class RailguardsConfig(BaseSettings):
    # read_only (default) denies all writes; read_write enables them subject to
    # the remaining rules.
    access_level: str = "read_only"
    allowed_recipients: list[str] = []
    blocked_actions: list[str] = []
    rate_limits: dict[str, int] = {}
    archive_first_policy: bool = False


class MCPConfig(BaseSettings):
    server_name: str = "Gmail-MCP"
    # Transport for AI-agent harnesses: "stdio" (default) or "http"
    # (streamable HTTP), served on host:port.
    transport: str = "stdio"
    host: str = "127.0.0.1"
    port: int = 8080


class LLMConfig(BaseSettings):
    provider: str = "openai"
    model: str = "gpt-4"
    api_key: str = ""
    # OpenAI-compatible HTTP endpoint (remote inference); empty uses the
    # official OpenAI base URL.
    base_url: str = ""
    # Local llama.cpp model path (used when provider is "llamacpp").
    model_path: str = ""


class SearchConfig(BaseSettings):
    # Vector backend: "sqlite_vss" (default) or "pgvector".
    backend: str = "sqlite_vss"
    embedding_model: str = "BAAI/bge-small-en-v1.5"
    embedding_dimension: int = 384


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
    search: SearchConfig = SearchConfig()
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
