# domain-events Specification

## Purpose
Defines the domain-event model and EventBus used for decoupled, in-process communication between bounded contexts.

## Requirements

### Requirement: DomainEvent base carries metadata
`DomainEvent` SHALL provide `event_id` (UUID), `occurred_at` (datetime), and `aggregate_id` fields.

#### Scenario: Event creation
- **WHEN** a domain event is instantiated with an `aggregate_id`
- **THEN** it has a unique `event_id`, current `occurred_at`, and the provided `aggregate_id`

### Requirement: EventBus protocol defines publish/subscribe
`EventBus` SHALL define `publish(event)`, `subscribe(event_type, handler)`, and `publish_all(events)`.

#### Scenario: Subscribe and publish
- **WHEN** a handler is subscribed to an event type and an event is published
- **THEN** the handler is invoked with the event

#### Scenario: Multiple handlers
- **WHEN** multiple handlers are subscribed to the same event type
- **THEN** all handlers are invoked when an event is published

#### Scenario: Publish all
- **WHEN** `publish_all(events)` is called with a list of events
- **THEN** each event is dispatched to its subscribed handlers

### Requirement: InMemoryEventBus provides in-memory implementation
`InMemoryEventBus` SHALL implement `EventBus` with synchronous, in-memory dispatch.

#### Scenario: In-memory publish
- **WHEN** an event is published to `InMemoryEventBus`
- **THEN** subscribed handlers receive the event synchronously

#### Scenario: Event ordering
- **WHEN** multiple events are published in sequence
- **THEN** handlers receive them in publication order
