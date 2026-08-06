# notification-domain Specification

## Purpose
Defines the Notification bounded context's domain model — inbox/digest events and the notification gateway port.

## Requirements

### Requirement: ImportantEmailDetected event
The system SHALL define ImportantEmailDetected domain event for high-priority email notifications.

#### Scenario: ImportantEmailDetected event created
- **WHEN** an ImportantEmailDetected event is instantiated
- **THEN** it contains email_id, from_address, subject, priority, and detected_at

#### Scenario: Event priority is valid
- **WHEN** an ImportantEmailDetected event is created with priority outside 1-5
- **THEN** a ValidationError is raised

### Requirement: InboxChanged event
The system SHALL define InboxChanged domain event for inbox state changes.

#### Scenario: InboxChanged event created
- **WHEN** an InboxChanged event is instantiated
- **THEN** it contains event_type, email_id, and changed_at

### Requirement: DigestReady event
The system SHALL define DigestReady domain event for periodic email digests.

#### Scenario: DigestReady event created
- **WHEN** a DigestReady event is instantiated
- **THEN** it contains digest_type, digest_period, email_count, and generated_at

#### Scenario: DigestReady valid digest types
- **WHEN** a DigestReady event is created with an invalid digest_type
- **THEN** a ValidationError is raised

### Requirement: NotificationGateway port
The system SHALL define NotificationGateway port with send and publish methods.

#### Scenario: Notification sent
- **WHEN** send(title, body, channel) is called on NotificationGateway
- **THEN** a boolean indicating success is returned

#### Scenario: Event published
- **WHEN** publish(event_type, payload) is called on NotificationGateway
- **THEN** a boolean indicating success is returned
