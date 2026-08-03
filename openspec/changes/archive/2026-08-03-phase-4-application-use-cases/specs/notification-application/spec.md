## ADDED Requirements

### Requirement: NotifyImportantEmailUseCase
The system SHALL provide NotifyImportantEmailUseCase that subscribes to the ImportantEmailDetected domain event and dispatches a notification through the NotificationGateway on the appropriate channel.

#### Scenario: Important email triggers a notification
- **WHEN** an ImportantEmailDetected event is published to the EventBus
- **THEN** NotifyImportantEmailUseCase handles it and calls NotificationGateway.send() with the email's title/body on the configured channel

#### Scenario: Notification dispatch failure is surfaced
- **WHEN** the NotificationGateway reports a failed send
- **THEN** the use case surfaces the failure rather than silently succeeding

### Requirement: PublishInboxEventUseCase
The system SHALL provide PublishInboxEventUseCase that subscribes to inbox-change domain events and publishes them to external notification channels via the NotificationGateway.

#### Scenario: Inbox change is published externally
- **WHEN** an inbox-change event (e.g., InboxChanged) is published to the EventBus
- **THEN** PublishInboxEventUseCase handles it and calls NotificationGateway.publish() with the event type and payload

#### Scenario: Routing to multiple channels
- **WHEN** the use case is configured with multiple channels and an inbox-change event occurs
- **THEN** the event payload is published to each configured channel
