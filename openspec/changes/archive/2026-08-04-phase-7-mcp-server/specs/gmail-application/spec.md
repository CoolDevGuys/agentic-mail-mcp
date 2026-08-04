## ADDED Requirements

### Requirement: AddLabelUseCase
The system SHALL provide a railguarded `AddLabelUseCase` that consumes an `AddLabelCommand`, is validated by the `RailguardValidator` before execution, applies the label via `GmailGateway.modify_message`, and emits an `EmailLabeled` event after the gateway call succeeds.

#### Scenario: Label applied when permitted
- **WHEN** `AddLabelUseCase` executes an `AddLabelCommand` and the railguard validation passes
- **THEN** the label is added via `GmailGateway.modify_message` and an `EmailLabeled` event is published to the event bus with the email id and label name

#### Scenario: Denied when access is read-only
- **WHEN** `AddLabelUseCase` executes while `access_level` is `read_only`
- **THEN** the `RailguardValidator` raises `PermissionError` and no gateway call or event publication occurs

#### Scenario: No event when gateway fails
- **WHEN** the gateway call raises during label application
- **THEN** the error propagates and no `EmailLabeled` event is published
