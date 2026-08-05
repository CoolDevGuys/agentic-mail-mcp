from src.Bootstrap.Settings import (
    DatabaseConfig,
    GmailConfig,
    LLMConfig,
    LoggingConfig,
    MCPConfig,
    NotificationsConfig,
    RailguardsConfig,
    Settings,
)


class TestGmailConfig:
    def test_default_values(self):
        config = GmailConfig()
        assert config.oauth_client_id == ""
        assert config.oauth_client_secret == ""
        assert config.scopes == ["https://www.googleapis.com/auth/gmail.modify"]
        assert config.token_storage_path == "token.json"
        assert config.token_encryption_key == ""

    def test_custom_values(self):
        config = GmailConfig(
            oauth_client_id="test-id",
            oauth_client_secret="test-secret",
            scopes=["scope1"],
            token_storage_path="/tmp/token.json",
            token_encryption_key="key",
        )
        assert config.oauth_client_id == "test-id"
        assert config.oauth_client_secret == "test-secret"
        assert config.scopes == ["scope1"]


class TestDatabaseConfig:
    def test_default_values(self):
        config = DatabaseConfig()
        assert config.url == "sqlite:///./gmail_mcp.db"
        assert config.driver == "sqlite"


class TestRailguardsConfig:
    def test_default_values(self):
        config = RailguardsConfig()
        assert config.access_level == "read_only"
        assert config.allowed_recipients == []
        assert config.blocked_actions == []
        assert config.rate_limits == {}
        assert config.archive_first_policy is False


class TestMCPConfig:
    def test_default_values(self):
        config = MCPConfig()
        assert config.server_name == "Gmail-MCP"
        assert config.host == "127.0.0.1"
        assert config.port == 8080


class TestLLMConfig:
    def test_default_values(self):
        config = LLMConfig()
        assert config.provider == "openai"
        assert config.model == "gpt-4"
        assert config.api_key == ""


class TestNotificationsConfig:
    def test_default_values(self):
        config = NotificationsConfig()
        assert config.webhook_url == ""
        assert config.redis_url == ""


class TestLoggingConfig:
    def test_default_values(self):
        config = LoggingConfig()
        assert config.level == "INFO"
        assert config.json_format is True


class TestSettings:
    def test_default_settings(self):
        settings = Settings()
        assert isinstance(settings.gmail, GmailConfig)
        assert isinstance(settings.database, DatabaseConfig)
        assert isinstance(settings.railguards, RailguardsConfig)
        assert isinstance(settings.mcp, MCPConfig)
        assert isinstance(settings.llm, LLMConfig)
        assert isinstance(settings.notifications, NotificationsConfig)
        assert isinstance(settings.logging, LoggingConfig)

    def test_from_env(self):
        settings = Settings.from_env()
        assert isinstance(settings, Settings)

    def test_nested_config_customization(self):
        settings = Settings(logging=LoggingConfig(level="DEBUG", json_format=False))
        assert settings.logging.level == "DEBUG"
        assert settings.logging.json_format is False

    def test_database_config_customization(self):
        settings = Settings(
            database=DatabaseConfig(url="postgresql://u:p@h/d", driver="asyncpg")
        )
        assert settings.database.url == "postgresql://u:p@h/d"
        assert settings.database.driver == "asyncpg"


class TestEnvironmentOverride:
    """Nested sections load from GMAIL_MCP_<SECTION>_<FIELD> env vars."""

    def test_env_overrides_across_sections(self, monkeypatch):
        monkeypatch.setenv("GMAIL_MCP_DATABASE_URL", "postgresql://u:p@h/d")
        monkeypatch.setenv("GMAIL_MCP_RAILGUARDS_ACCESS_LEVEL", "read_write")
        monkeypatch.setenv("GMAIL_MCP_MCP_TRANSPORT", "http")
        monkeypatch.setenv("GMAIL_MCP_MCP_PORT", "9999")
        monkeypatch.setenv("GMAIL_MCP_LLM_API_KEY", "sk-test")

        settings = Settings.from_env()

        assert settings.database.url == "postgresql://u:p@h/d"
        assert settings.railguards.access_level == "read_write"
        assert settings.mcp.transport == "http"
        assert settings.mcp.port == 9999
        assert settings.llm.api_key == "sk-test"

    def test_defaults_when_env_absent(self, monkeypatch):
        for var in (
            "GMAIL_MCP_DATABASE_URL",
            "GMAIL_MCP_RAILGUARDS_ACCESS_LEVEL",
            "GMAIL_MCP_MCP_TRANSPORT",
        ):
            monkeypatch.delenv(var, raising=False)

        settings = Settings.from_env()

        assert settings.database.url == "sqlite:///./gmail_mcp.db"
        assert settings.railguards.access_level == "read_only"
        assert settings.mcp.transport == "stdio"
