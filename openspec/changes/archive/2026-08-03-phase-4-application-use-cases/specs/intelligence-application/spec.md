## ADDED Requirements

### Requirement: SummarizeEmailUseCase
The system SHALL provide SummarizeEmailUseCase that accepts an email_id, calls the LlmGateway with a summarization prompt, persists a Summary entity, and returns a SummaryDTO.

#### Scenario: Summarize an email
- **WHEN** SummarizeEmailUseCase.execute is called with an email_id and the LlmGateway returns summary text
- **THEN** a Summary entity is persisted and a SummaryDTO with the summary text and model used is returned

#### Scenario: Summarize a missing email
- **WHEN** SummarizeEmailUseCase.execute is called with an email_id that cannot be resolved
- **THEN** a NotFoundError is raised

### Requirement: SuggestReplyUseCase
The system SHALL provide SuggestReplyUseCase that accepts an email_id, calls the LlmGateway with a reply-suggestion prompt, persists a Suggestion entity, and returns a SuggestionDTO.

#### Scenario: Suggest a reply
- **WHEN** SuggestReplyUseCase.execute is called with an email_id and the LlmGateway returns draft text
- **THEN** a Suggestion entity is persisted and a SuggestionDTO with the draft text is returned

### Requirement: ClassifyEmailUseCase
The system SHALL provide ClassifyEmailUseCase that accepts an email_id, calls the LlmGateway with a classification prompt, persists a Classification entity, and returns a ClassificationDTO with category and priority.

#### Scenario: Classify an email
- **WHEN** ClassifyEmailUseCase.execute is called with an email_id and the LlmGateway returns a category and priority
- **THEN** a Classification entity is persisted and a ClassificationDTO carrying category, priority, and confidence is returned

#### Scenario: Classification confidence recorded
- **WHEN** ClassifyEmailUseCase.execute produces a classification
- **THEN** the returned ClassificationDTO includes the model's confidence score

### Requirement: Digest use cases
The system SHALL provide DailyDigestUseCase and WeeklyDigestUseCase that query unread/important emails for the relevant time period, call the LlmGateway to generate a digest, return a DigestDTO of grouped summaries, and publish a DigestReady event.

#### Scenario: Generate a daily digest
- **WHEN** DailyDigestUseCase.execute is called for a given date
- **THEN** it selects emails within that day, produces a DigestDTO of grouped summaries, and publishes a DigestReady event to the EventBus

#### Scenario: Generate a weekly digest
- **WHEN** WeeklyDigestUseCase.execute is called for a given week start
- **THEN** it selects emails within that week and returns a DigestDTO covering the period

#### Scenario: Digest time filtering uses the injected clock
- **WHEN** a digest use case runs with a fixed test clock
- **THEN** the time window used for selecting emails is derived deterministically from the injected clock

### Requirement: ExtractActionItemsUseCase
The system SHALL provide ExtractActionItemsUseCase that accepts an email_id, calls the LlmGateway to extract action items, and returns a list of ActionItemDTO with description, due_date, and priority.

#### Scenario: Extract action items
- **WHEN** ExtractActionItemsUseCase.execute is called with an email_id and the LlmGateway returns action items
- **THEN** the use case returns a list of ActionItemDTO carrying description, optional due_date, and priority

#### Scenario: Email with no action items
- **WHEN** ExtractActionItemsUseCase.execute is called and the LlmGateway returns none
- **THEN** the use case returns an empty list without error
