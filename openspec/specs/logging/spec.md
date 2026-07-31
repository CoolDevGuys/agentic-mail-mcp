## ADDED Requirements

### Requirement: Structured JSON logging setup
The Logging module SHALL provide a setup_logging(level, json_format) function that configures application-wide JSON logging.

#### Scenario: Logging is configured
- **WHEN** setup_logging("INFO", True) is called
- **THEN** root logger outputs JSON-formatted messages

### Requirement: JSON log format
Each log entry SHALL include correlation_id, timestamp, level, module, and message fields.

#### Scenario: Log entry has required fields
- **WHEN** a log message is emitted
- **THEN** the JSON output contains correlation_id, timestamp, level, module, and message keys

### Requirement: Sensitive data redaction
The logger SHALL mask values matching patterns for tokens, passwords, and email bodies.

#### Scenario: Token values are redacted
- **WHEN** a log message contains "Bearer eyJ..."
- **THEN** the output shows the value masked (e.g., "[REDACTED]")

### Requirement: Configurable log level
The logging level SHALL be configurable via Settings.logging.level.

#### Scenario: Level follows settings
- **WHEN** Settings.logging.level is "DEBUG"
- **THEN** debug-level messages are emitted
