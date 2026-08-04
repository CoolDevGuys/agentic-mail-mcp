## MODIFIED Requirements

### Requirement: Dockerfile with Python 3.11 slim
The Dockerfile SHALL be a multi-stage build: a builder stage that installs build dependencies and produces a wheel, and a `python:3.11-slim` runtime stage that installs only the built package, runs as a non-root user, and contains no build toolchain.

#### Scenario: Dockerfile stages
- **WHEN** the Dockerfile is parsed
- **THEN** it defines a builder stage that builds the package and a `python:3.11-slim` runtime stage
- **THEN** the runtime stage installs the built package and runs as a non-root user

#### Scenario: Runtime image excludes build toolchain
- **WHEN** the runtime stage is inspected
- **THEN** it copies the built artifact from the builder rather than installing build tools

## ADDED Requirements

### Requirement: Multi-architecture build
The image SHALL be buildable for both `linux/amd64` and `linux/arm64`.

#### Scenario: Multi-arch build documented and supported
- **WHEN** the release documentation is read
- **THEN** it describes building the image for `linux/amd64` and `linux/arm64` (e.g. via `docker buildx`)

#### Scenario: Dockerfile is architecture-agnostic
- **WHEN** the Dockerfile is parsed
- **THEN** it pins no architecture-specific base image or dependency that would prevent an arm64 or amd64 build
