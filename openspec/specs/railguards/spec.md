# railguards Specification

## Purpose
TBD - created by archiving change phase-6-railguards-framework. Update Purpose after archive.
## Requirements
### Requirement: Railguard configuration model
The system SHALL provide a railguard configuration model with `access_level` (`read_only` or `read_write`), `allowed_recipients`, `blocked_actions`, `rate_limits`, and `archive_first_policy`, parsed from the `Settings.railguards` section. The access level SHALL default to `read_only` when unset.

#### Scenario: Default access level is read_only
- **WHEN** the railguard configuration is built with no access level configured
- **THEN** the access level is `read_only`

#### Scenario: Invalid access level is rejected
- **WHEN** the railguard configuration is built with an access level outside {read_only, read_write}
- **THEN** a ValidationError is raised

#### Scenario: Allowed recipients accept address or domain
- **WHEN** `allowed_recipients` contains a full address and a domain (e.g. `@example.com`)
- **THEN** the configuration matches recipients by exact address or by domain suffix

### Requirement: RailguardValidator denies writes when read-only
The RailguardValidator SHALL deny every write command when the access level is `read_only`, regardless of other rules, and raise PermissionError.

#### Scenario: Write denied under read-only
- **WHEN** validate is called with any write command and access_level is `read_only`
- **THEN** a RailguardResult with allowed=False is produced and PermissionError is raised

#### Scenario: Write permitted under read-write when other rules pass
- **WHEN** validate is called with a write command, access_level is `read_write`, and no other rule is violated
- **THEN** a RailguardResult with allowed=True is produced and no error is raised

### Requirement: RailguardValidator enforces recipient allowlist
The RailguardValidator SHALL deny a forward command whose recipient is not in the allowed recipients (by exact address or domain) when an allowlist is configured.

#### Scenario: Recipient not in allowlist is denied
- **WHEN** a forward command targets a recipient absent from a configured allowlist
- **THEN** the result is denied with a reason and PermissionError is raised

#### Scenario: Recipient in allowlist is permitted
- **WHEN** a forward command targets a recipient present in the allowlist (by address or domain)
- **THEN** the result is allowed

#### Scenario: Empty allowlist does not restrict recipients
- **WHEN** no allowlist is configured and a forward command is validated
- **THEN** the recipient check does not deny the command

### Requirement: RailguardValidator enforces action blocklist
The RailguardValidator SHALL deny a command whose action is present in the blocked actions.

#### Scenario: Blocked action is denied
- **WHEN** a command's action (e.g. `permanent_delete`) is in the blocked actions
- **THEN** the result is denied and PermissionError is raised

### Requirement: RailguardValidator enforces rate limits
The RailguardValidator SHALL deny a command whose action would exceed its configured maximum operations within the trailing time window, measured against the injected clock.

#### Scenario: Rate limit exceeded is denied
- **WHEN** the number of operations for an action within the window already equals its configured maximum
- **THEN** the next command for that action is denied and PermissionError is raised

#### Scenario: Operations outside the window do not count
- **WHEN** prior operations fall outside the trailing window per the clock
- **THEN** they do not count toward the limit and the command is allowed

### Requirement: RailguardValidator enforces archive-first policy
When the archive-first policy is enabled, the RailguardValidator SHALL deny a permanent delete of an email that has not been archived.

#### Scenario: Permanent delete of non-archived email is denied
- **WHEN** archive-first is enabled and a permanent delete targets an email still in the inbox
- **THEN** the result is denied and PermissionError is raised

#### Scenario: Permanent delete of archived email is permitted
- **WHEN** archive-first is enabled and the target email is already archived
- **THEN** the archive-first check does not deny the command

