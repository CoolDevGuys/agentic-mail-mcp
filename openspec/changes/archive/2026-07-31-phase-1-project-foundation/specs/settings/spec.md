## ADDED Requirements

### Requirement: Settings class with pydantic-settings
The Settings class SHALL inherit from pydantic_settings.BaseSettings and provide typed configuration for all application sections.

#### Scenario: Settings inherits from BaseSettings
- **WHEN** Settings class is inspected
- **THEN** its MRO includes pydantic_settings.BaseSettings

### Requirement: Configuration sections
The Settings class SHALL define sections: gmail (OAuth client ID/secret, scopes, token_storage_path, token_encryption_key), database (URL, driver), railguards (access_level, allowed_recipients, blocked_actions, rate_limits), mcp (server_name, host, port), llm (provider, model, api_key), notifications (webhook_url, redis_url).

#### Scenario: All sections are present
- **WHEN** Settings model fields are listed
- **THEN** gmail, database, railguards, mcp, llm, and notifications sections exist

### Requirement: Environment variable support
The Settings class SHALL support loading from .env files and environment variables prefixed with GMAIL_MCP_.

#### Scenario: ENV vars override defaults
- **WHEN** GMAIL_MCP_DATABASE_URL is set
- **THEN** Settings.database.url reflects the environment value

### Requirement: Factory method
The Settings class SHALL provide a from_env() class method as a factory for loading configuration.

#### Scenario: Factory creates instance
- **WHEN** Settings.from_env() is called
- **THEN** a fully populated Settings instance is returned

### Requirement: .env.example file
The project SHALL include a .env.example file documenting all configuration keys without real secrets.

#### Scenario: Template file exists
- **WHEN** .env.example is read
- **THEN** all Settings keys are documented with placeholder values
