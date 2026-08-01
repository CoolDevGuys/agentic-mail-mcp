## ADDED Requirements

### Requirement: Summary entity
The system SHALL model Summary as an entity containing an AI-generated email summary.

#### Scenario: Summary created with required fields
- **WHEN** a Summary is created with email_id, summary_text, and model_used
- **THEN** the entity is created with created_at timestamp

#### Scenario: Summary requires non-empty text
- **WHEN** a Summary is created with empty summary_text
- **THEN** a ValidationError is raised

### Requirement: Classification entity
The system SHALL model Classification as an entity with email category, priority, and confidence.

#### Scenario: Classification created with valid category
- **WHEN** a Classification is created with category="urgent", priority=5, confidence=0.95
- **THEN** the entity is created successfully

#### Scenario: Classification priority within range
- **WHEN** a Classification is created with priority=6
- **THEN** a ValidationError is raised (priority must be 1-5)

#### Scenario: Classification confidence within range
- **WHEN** a Classification is created with confidence=1.5
- **THEN** a ValidationError is raised (confidence must be 0.0-1.0)

#### Scenario: Classification valid categories
- **WHEN** a Classification is created with category="unknown"
- **THEN** a ValidationError is raised (must be urgent/normal/spam/promo)

### Requirement: Suggestion entity
The system SHALL model Suggestion as an entity with AI-generated reply or action suggestions.

#### Scenario: Suggestion created with valid type
- **WHEN** a Suggestion is created with suggestion_type="reply" and draft_text
- **THEN** the entity is created successfully

#### Scenario: Suggestion type validation
- **WHEN** a Suggestion is created with suggestion_type="custom"
- **THEN** a ValidationError is raised (must be reply/forward/ignore)

### Requirement: PromptTemplate value object
The system SHALL provide PromptTemplate with render capability for variable substitution.

#### Scenario: Template rendered with variables
- **WHEN** PromptTemplate.render(subject="Hello", body="World") is called on a template with "{subject}: {body}"
- **THEN** the rendered string is "Hello: World"

#### Scenario: Template rendering fails on missing variable
- **WHEN** PromptTemplate.render() is called without providing "{missing}" variable
- **THEN** a ValidationError is raised

### Requirement: ModelConfig value object
The system SHALL provide ModelConfig with LLM provider, model ID, max tokens, and temperature.

#### Scenario: ModelConfig created with valid values
- **WHEN** a ModelConfig is created with provider, model_id, max_tokens=1000, temperature=0.7
- **THEN** the value object is created successfully

#### Scenario: ModelConfig max_tokens positive
- **WHEN** a ModelConfig is created with max_tokens=0
- **THEN** a ValidationError is raised

#### Scenario: ModelConfig temperature within range
- **WHEN** a ModelConfig is created with temperature=2.0
- **THEN** a ValidationError is raised (temperature must be 0.0-1.0)

### Requirement: LlmGateway port
The system SHALL define LlmGateway port with generate method for LLM interactions.

#### Scenario: LLM prompt generated
- **WHEN** generate(prompt, system_prompt, max_tokens, model) is called
- **THEN** an LlmResponse with text, model, and usage is returned

#### Scenario: LlmResponse contains usage metrics
- **WHEN** an LlmResponse is returned
- **THEN** it includes input_tokens and output_tokens in usage
