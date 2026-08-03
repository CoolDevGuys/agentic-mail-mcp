# intelligence-llm-adapter Specification

## Purpose
TBD - created by archiving change phase-5-infrastructure-adapters. Update Purpose after archive.
## Requirements
### Requirement: LlmGateway implementation over llama.cpp or OpenAI-compatible API
The system SHALL provide a LlamaCppGateway that implements the LlmGateway port, targeting either a local llama.cpp model or a remote OpenAI-compatible endpoint, selected by configuration.

#### Scenario: Generate returns an LlmResponse
- **WHEN** LlamaCppGateway.generate is called with a prompt, system prompt, max tokens, and model
- **THEN** it returns an LlmResponse containing the generated text, the model used, and token usage

#### Scenario: Remote endpoint configuration is used
- **WHEN** the gateway is configured with an OpenAI-compatible base URL and API key
- **THEN** generate issues the request to that endpoint and maps the response to LlmResponse

#### Scenario: Local model path configuration is used
- **WHEN** the gateway is configured with a local model path
- **THEN** generate runs inference against the local model without a network call

#### Scenario: Generation failure surfaces a domain error
- **WHEN** the underlying provider returns an error
- **THEN** the gateway raises a domain error rather than leaking the provider exception

