## ADDED Requirements

### Requirement: SearchDocument entity
The system SHALL model SearchDocument as an entity containing indexable text, embedding vector, and metadata.

#### Scenario: SearchDocument created with embedding
- **WHEN** a SearchDocument is created with email_id, content, embedding vector, and metadata
- **THEN** the entity is created successfully

#### Scenario: SearchDocument embedding dimension validation
- **WHEN** a SearchDocument is created with an embedding vector of wrong dimension
- **THEN** a ValidationError is raised

### Requirement: EmbeddingGateway port
The system SHALL define EmbeddingGateway port with embed and dimension methods.

#### Scenario: Text embedded
- **WHEN** embed(text) is called on EmbeddingGateway
- **THEN** a list of floats representing the embedding vector is returned

#### Scenario: Embedding dimension reported
- **WHEN** dimension() is called on EmbeddingGateway
- **THEN** the embedding vector dimension is returned as an integer

### Requirement: VectorSearchRepository port
The system SHALL define VectorSearchRepository protocol with index, search, delete, and count operations.

#### Scenario: Document indexed
- **WHEN** index(document) is called on VectorSearchRepository
- **THEN** the document is stored for similarity search

#### Scenario: Similarity search returns results
- **WHEN** search(query_vector, limit=10, min_score=0.8) is called
- **THEN** a list of SearchResult objects with score >= min_score is returned (up to limit)

#### Scenario: SearchResult contains required fields
- **WHEN** a SearchResult is returned from search
- **THEN** it includes document_id, email_id, score, and metadata

#### Scenario: Document deleted by email ID
- **WHEN** delete(email_id) is called
- **THEN** the document associated with that email is removed

#### Scenario: Index count reported
- **WHEN** count() is called
- **THEN** the total number of indexed documents is returned
