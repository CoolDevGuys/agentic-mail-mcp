## ADDED Requirements

### Requirement: Railguards access level and archive-first policy
The railguards configuration section SHALL expose an `access_level` field taking the values `read_only` or `read_write` and defaulting to `read_only`, and an `archive_first_policy` flag defaulting to false.

#### Scenario: Access level defaults to read_only
- **WHEN** Settings is built with no railguards access level configured
- **THEN** railguards.access_level is `read_only`

#### Scenario: Railguards section exposes archive_first_policy
- **WHEN** the railguards section fields are listed
- **THEN** archive_first_policy is present alongside access_level, allowed_recipients, blocked_actions, and rate_limits
