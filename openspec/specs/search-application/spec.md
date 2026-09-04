# search-application Specification

## Purpose
TBD - created by archiving change phase-4-application-use-cases. Update Purpose after archive.
## Requirements
### Requirement: SemanticSearchUseCase
The system SHALL provide SemanticSearchUseCase that accepts a natural-language query, vectorizes it via the EmbeddingGateway, performs a similarity search via the VectorSearchRepository, and returns a list of SearchResultDTO ordered by score. When an EmailRepository is wired, each result SHALL also carry the matched email's Gmail message id so callers can fetch the email directly.

#### Scenario: Semantic search returns scored results
- **WHEN** SemanticSearchUseCase.execute is called with a query, limit, and min_score
- **THEN** the query is embedded and the use case returns SearchResultDTOs whose scores are at least min_score, ordered by descending score

#### Scenario: Semantic search honors the result limit
- **WHEN** SemanticSearchUseCase.execute is called with a limit
- **THEN** at most that many SearchResultDTOs are returned

#### Scenario: No matches above threshold
- **WHEN** no indexed document scores at or above min_score
- **THEN** the use case returns an empty list

#### Scenario: Result carries the Gmail message id when resolvable
- **WHEN** the use case is wired with an EmailRepository and a matched result's email id resolves to a stored email
- **THEN** the SearchResultDTO's message_id is that email's Gmail message id

#### Scenario: Unresolvable email leaves message id null
- **WHEN** no EmailRepository is wired, or a matched email id is not present in the repository
- **THEN** the SearchResultDTO's message_id is null

### Requirement: IndexEmailUseCase
The system SHALL provide IndexEmailUseCase that accepts an email_id, extracts indexable text, creates an embedding via the EmbeddingGateway, and persists a SearchDocument via the VectorSearchRepository.

#### Scenario: Index an email
- **WHEN** IndexEmailUseCase.execute is called with an email_id
- **THEN** the email's indexable text is embedded and a SearchDocument is persisted via the VectorSearchRepository

#### Scenario: Embedding dimension matches repository
- **WHEN** IndexEmailUseCase builds an embedding
- **THEN** the embedding dimension matches EmbeddingGateway.dimension() before the document is indexed

### Requirement: RebuildIndexUseCase
The system SHALL provide RebuildIndexUseCase that iterates all indexed emails, re-embeds and re-indexes each, and returns rebuild statistics.

#### Scenario: Rebuild the full index
- **WHEN** RebuildIndexUseCase.execute is called
- **THEN** every indexed email is re-embedded and re-indexed and the use case returns statistics including the count of documents rebuilt

#### Scenario: Rebuild with an empty index
- **WHEN** RebuildIndexUseCase.execute is called and there are no documents
- **THEN** the use case returns statistics with a zero rebuilt count and no error

