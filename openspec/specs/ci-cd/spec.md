## ADDED Requirements

### Requirement: GitHub Actions CI workflow
The project SHALL include a GitHub Actions workflow that runs lint (ruff), type-check (mypy), and test (pytest with coverage) on every push and PR.

#### Scenario: CI runs on push
- **WHEN** code is pushed to the repository
- **THEN** the CI workflow triggers lint, type-check, and test jobs

### Requirement: Dependency vulnerability scanning
The project SHALL include scheduled dependency vulnerability scanning (pip-audit or GitHub Dependabot).

#### Scenario: Scanning runs on schedule
- **WHEN** the scheduled trigger fires
- **THEN** dependency vulnerabilities are reported

### Requirement: Lockfile validation
The CI SHALL validate that the committed lockfile matches the current dependencies.

#### Scenario: Lockfile drift detected
- **WHEN** the lockfile is out of sync with pyproject.toml
- **THEN** CI fails with a lockfile validation error

### Requirement: Release publishing
The project SHALL have a build/publish job gated on CI green, triggered on release tag.

#### Scenario: Release triggers publish
- **WHEN** a release tag is pushed and CI passes
- **THEN** the build/publish job executes
