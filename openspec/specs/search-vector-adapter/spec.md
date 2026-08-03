# search-vector-adapter Specification

## Purpose
TBD - created by archiving change phase-5-infrastructure-adapters. Update Purpose after archive.
## Requirements
### Requirement: BGE embedding gateway
The system SHALL provide a BgeEmbeddingGateway that implements the EmbeddingGateway port, producing embeddings whose length equals its reported dimension.

#### Scenario: Embed returns a vector of the reported dimension
- **WHEN** BgeEmbeddingGateway.embed is called with text
- **THEN** it returns a list of floats whose length equals BgeEmbeddingGateway.dimension()

#### Scenario: Deterministic embedding for identical input
- **WHEN** the same text is embedded twice
- **THEN** the two vectors are equal

### Requirement: sqlite-vss vector repository (default)
The system SHALL provide a SqliteVssRepository that implements the VectorSearchRepository port using sqlite-vss as the default vector backend.

#### Scenario: Index then search returns the document by similarity
- **WHEN** a document is indexed and a query vector close to it is searched
- **THEN** the document is returned as a SearchResult above the score threshold

#### Scenario: Delete removes a document from results
- **WHEN** an indexed document is deleted and then searched for
- **THEN** it no longer appears in the results and count decreases

### Requirement: pgvector vector repository (optional)
The system SHALL provide a PgVectorRepository that implements the VectorSearchRepository port using the pgvector extension, available only when the PostgreSQL extra is installed.

#### Scenario: pgvector repository satisfies the vector contract
- **WHEN** the shared VectorSearchRepository contract test runs against the pgvector implementation
- **THEN** it passes the same assertions as the sqlite-vss implementation

### Requirement: Vector backends are interchangeable
The system SHALL verify that all VectorSearchRepository implementations satisfy one shared contract test suite so backends can be swapped without changing callers.

#### Scenario: Both backends pass the same contract
- **WHEN** the parametrized contract test suite runs against both the sqlite-vss and pgvector implementations
- **THEN** both produce identical observable behavior for index, search, delete, and count

