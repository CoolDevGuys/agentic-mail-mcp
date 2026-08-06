# settings Specification

## Purpose
TBD - normalized during phase-6 archive. Update Purpose after archive.
## Requirements
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
The Settings class SHALL support loading from .env files and environment variables prefixed with AGENTIC_MAIL_MCP_.

#### Scenario: ENV vars override defaults
- **WHEN** AGENTIC_MAIL_MCP_DATABASE_URL is set
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

### Requirement: Railguards access level and archive-first policy
The railguards configuration section SHALL expose an `access_level` field taking the values `read_only` or `read_write` and defaulting to `read_only`, and an `archive_first_policy` flag defaulting to false.

#### Scenario: Access level defaults to read_only
- **WHEN** Settings is built with no railguards access level configured
- **THEN** railguards.access_level is `read_only`

#### Scenario: Railguards section exposes archive_first_policy
- **WHEN** the railguards section fields are listed
- **THEN** archive_first_policy is present alongside access_level, allowed_recipients, blocked_actions, and rate_limits

