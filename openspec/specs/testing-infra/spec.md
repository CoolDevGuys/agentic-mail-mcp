# testing-infra Specification

## Purpose
Defines the testing infrastructure: pytest configuration, shared fixtures, fakes, directory layout, and coverage floors.

## Requirements

### Requirement: pytest configuration
The project SHALL include pytest.ini with asyncio_mode=auto, testpaths, and markers configuration.

#### Scenario: pytest reads config
- **WHEN** pytest runs
- **THEN** async tests work without explicit @pytest.mark.asyncio

### Requirement: Shared test fixtures
The tests/conftest.py SHALL provide fixtures for settings, event_bus, clock, and container.

#### Scenario: Fixtures are available
- **WHEN** a test function requests the settings fixture
- **THEN** it receives a valid Settings instance

### Requirement: Test directory structure
The project SHALL have tests/unit/, tests/integration/, and tests/fakes/ directories.

#### Scenario: Directories exist
- **WHEN** tests/ is listed
- **THEN** unit/, integration/, and fakes/ subdirectories exist

### Requirement: Fake implementations
The tests/fakes/ directory SHALL contain in-memory fakes: FakeEmailRepository, FakeLlmGateway, FakeEmbeddingGateway, FakeNotificationGateway, and a GmailGateway stub (StubGmailGateway in ports.py).

#### Scenario: Fakes exist
- **WHEN** tests/fakes/ is listed
- **THEN** all fakes are present, including the StubGmailGateway in ports.py

### Requirement: Coverage floors
The project SHALL enforce tiered coverage: >=90% on Domain/ directories, >=80% overall. CI SHALL fail below either floor.

#### Scenario: Coverage check fails below floor
- **WHEN** Domain/ coverage is 85%
- **THEN** CI fails the build
