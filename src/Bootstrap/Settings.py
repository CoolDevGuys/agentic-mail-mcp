from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _section_config(prefix: str) -> SettingsConfigDict:
    """Config for a settings section: read ``GMAIL_MCP_<SECTION>_<FIELD>`` from
    the environment or a ``.env`` file. Each section carries its own prefix so a
    flat single-underscore env var maps onto the nested field."""
    return SettingsConfigDict(
        env_prefix=prefix,
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


class GmailConfig(BaseSettings):
    model_config = _section_config("GMAIL_MCP_GMAIL_")

    # Bring-your-own Google app. Either point at the OAuth client JSON you
    # download from Google Cloud (recommended — no copy-pasting secrets)…
    client_secrets_file: str = ""
    # …or set the client id/secret directly.
    oauth_client_id: str = ""
    oauth_client_secret: str = ""
    scopes: list[str] = ["https://www.googleapis.com/auth/gmail.modify"]
    token_storage_path: str = "token.json"
    token_encryption_key: str = ""


class DatabaseConfig(BaseSettings):
    model_config = _section_config("GMAIL_MCP_DATABASE_")

    # Synchronous driver: the repository ports and use cases (Phases 3-4) are
    # synchronous, so the persistence layer uses synchronous SQLAlchemy.
    url: str = "sqlite:///./gmail_mcp.db"
    driver: str = "sqlite"
    # Read-through email cache TTL (seconds). The cache stores metadata only
    # (never bodies) and is refreshed live per-email; this bounds how long list
    # views may serve recently-seen metadata. Gmail stays the source of truth.
    cache_ttl_seconds: int = 900


class RailguardsConfig(BaseSettings):
    model_config = _section_config("GMAIL_MCP_RAILGUARDS_")

    # read_only (default) denies all writes; read_write enables them subject to
    # the remaining rules.
    access_level: str = "read_only"
    allowed_recipients: list[str] = []
    blocked_actions: list[str] = []
    rate_limits: dict[str, int] = {}
    archive_first_policy: bool = False


class MCPConfig(BaseSettings):
    model_config = _section_config("GMAIL_MCP_MCP_")

    server_name: str = "Gmail-MCP"
    # Transport for AI-agent harnesses: "stdio" (default) or "http"
    # (streamable HTTP), served on host:port.
    transport: str = "stdio"
    host: str = "127.0.0.1"
    port: int = 8080


class LLMConfig(BaseSettings):
    model_config = _section_config("GMAIL_MCP_LLM_")

    provider: str = "openai"
    model: str = "gpt-4"
    api_key: str = ""
    # OpenAI-compatible HTTP endpoint (remote inference); empty uses the
    # official OpenAI base URL.
    base_url: str = ""
    # Local llama.cpp model path (used when provider is "llamacpp").
    model_path: str = ""
    # Caller-first by default: the calling agent is itself an LLM, so per-email
    # reasoning (summarize/classify/reply/action-items) is exposed as MCP prompts
    # the caller runs, not as internal-inference tools. Set true to also register
    # those as server-side tools (adds latency + needs a configured LLM).
    internal_tools: bool = False


class SearchConfig(BaseSettings):
    model_config = _section_config("GMAIL_MCP_SEARCH_")

    # Vector backend: "sqlite_vss" (default) or "pgvector".
    backend: str = "sqlite_vss"
    embedding_model: str = "BAAI/bge-small-en-v1.5"
    embedding_dimension: int = 384


class NotificationsConfig(BaseSettings):
    model_config = _section_config("GMAIL_MCP_NOTIFICATIONS_")

    webhook_url: str = ""
    redis_url: str = ""


class LoggingConfig(BaseSettings):
    model_config = _section_config("GMAIL_MCP_LOGGING_")

    level: str = "INFO"
    json_format: bool = True


class Settings(BaseSettings):
    gmail: GmailConfig = Field(default_factory=GmailConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    railguards: RailguardsConfig = Field(default_factory=RailguardsConfig)
    mcp: MCPConfig = Field(default_factory=MCPConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    search: SearchConfig = Field(default_factory=SearchConfig)
    notifications: NotificationsConfig = Field(default_factory=NotificationsConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)

    model_config = SettingsConfigDict(
        env_prefix="GMAIL_MCP_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @classmethod
    def from_env(cls) -> "Settings":
        return cls()
