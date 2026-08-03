# notification-channels-adapter Specification

## Purpose
TBD - created by archiving change phase-5-infrastructure-adapters. Update Purpose after archive.
## Requirements
### Requirement: Webhook notification gateway
The system SHALL provide a WebhookNotificationGateway that implements the NotificationGateway port by POSTing notification payloads to configured URLs.

#### Scenario: Successful POST returns true
- **WHEN** WebhookNotificationGateway.send or publish posts a payload and the endpoint responds with success
- **THEN** the method returns True

#### Scenario: Failed POST returns false
- **WHEN** the endpoint responds with an error or is unreachable
- **THEN** the method returns False rather than raising

### Requirement: Redis notification gateway
The system SHALL provide a RedisNotificationGateway that implements the NotificationGateway port using Redis pub/sub, available only when the notifications extra is installed.

#### Scenario: Publish delivers to subscribers
- **WHEN** RedisNotificationGateway.publish is called for a topic with an active subscriber
- **THEN** the subscriber receives the message and the method returns True

#### Scenario: Publish failure returns false
- **WHEN** the Redis connection is unavailable
- **THEN** publish returns False rather than raising

