## ADDED Requirements

### Requirement: DI container with registration
The DependencyContainer SHALL provide register(), resolve(), and singleton() methods for service management.

#### Scenario: Service is registered and resolved
- **WHEN** container.register(MyService) is called
- **THEN** container.resolve(MyService) returns a MyService instance

### Requirement: Factory and async factory support
The container SHALL support both sync factory functions and async factory functions.

#### Scenario: Async factory resolves
- **WHEN** an async factory is registered
- **THEN** await container.resolve(Service) returns the awaited instance

### Requirement: Pre-registered services
The container SHALL come pre-registered with: settings, logger, DB session factory, and event bus.

#### Scenario: Default services available
- **WHEN** a new Container is created
- **THEN** resolve(Settings), resolve(Logger), resolve(EventBus) succeed

### Requirement: Type-hinted resolution
The container SHALL use type hints for service resolution.

#### Scenario: Type-based resolution
- **WHEN** container.resolve(SomeProtocol) is called
- **THEN** the registered implementation of SomeProtocol is returned
