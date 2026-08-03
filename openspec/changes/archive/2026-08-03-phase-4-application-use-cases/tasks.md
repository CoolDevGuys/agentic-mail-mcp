## 1. Gmail Application: Query & Command Objects

- [x] 1.1 Implement read query objects: SearchEmailsQuery, GetEmailQuery, GetThreadQuery, ListUnreadQuery, ListLabelsQuery with field validation
- [x] 1.2 Write tests for query validation (invalid pagination, invalid label_type, UUID vs GmailMessageId in GetEmailQuery)
- [x] 1.3 Implement command objects: ForwardEmailCommand, ArchiveEmailCommand, DeleteEmailCommand, CreateDraftCommand, SendDraftCommand, AddLabelCommand, MarkReadCommand with validation (execution handlers deferred to Phase 6)
- [x] 1.4 Write tests for command validation (required recipient, permanent defaults to False, required email_id/label_name)

## 2. Gmail Application: DTOs

- [x] 2.1 Implement EmailDTO, ThreadDTO, LabelDTO as plain dataclasses
- [x] 2.2 Implement entity→DTO mapping helpers (Email→EmailDTO, Thread→ThreadDTO, Label→LabelDTO)
- [x] 2.3 Write tests for DTO mapping correctness

## 3. Gmail Application: Read Use Cases

- [x] 3.1 Implement SearchEmailsUseCase (build GmailQuery, live-gateway vs cached-repository source, SearchEmailsResult with pagination)
- [x] 3.2 Write tests for SearchEmailsUseCase (query combinations, empty results, pagination, cache-source mode, error handling)
- [x] 3.3 Implement GetEmailUseCase (resolve by UUID from repo or GmailMessageId via gateway, cache-miss fallback, body included)
- [x] 3.4 Write tests for GetEmailUseCase (UUID hit, cache miss → gateway, not found)
- [x] 3.5 Implement GetThreadUseCase (resolve thread with ordered email IDs → ThreadDTO)
- [x] 3.6 Write tests for GetThreadUseCase (happy path, not found)
- [x] 3.7 Implement ListUnreadUseCase (paginated unread EmailDTOs, optional label filter)
- [x] 3.8 Write tests for ListUnreadUseCase (with/without label, pagination)
- [x] 3.9 Implement ListLabelsUseCase (LabelDTOs filtered by system/user/all)
- [x] 3.10 Write tests for ListLabelsUseCase (all filter types)

## 4. Intelligence Application: Use Cases & DTOs

- [x] 4.1 Implement SummaryDTO, SuggestionDTO, ClassificationDTO, DigestDTO, ActionItemDTO
- [x] 4.2 Implement SummarizeEmailUseCase (LLM summarization prompt, persist Summary, return SummaryDTO)
- [x] 4.3 Write tests for SummarizeEmailUseCase (fake LLM, persistence verification, missing email)
- [x] 4.4 Implement SuggestReplyUseCase (LLM reply prompt, persist Suggestion, return SuggestionDTO)
- [x] 4.5 Write tests for SuggestReplyUseCase (fake LLM)
- [x] 4.6 Implement ClassifyEmailUseCase (LLM classification prompt, persist Classification, return ClassificationDTO with category/priority/confidence)
- [x] 4.7 Write tests for ClassifyEmailUseCase (all categories, confidence recorded)
- [x] 4.8 Implement DailyDigestUseCase and WeeklyDigestUseCase (time-windowed query via injected Clock, LLM digest, DigestDTO, publish DigestReady)
- [x] 4.9 Write tests for digest use cases (time filtering with TestClock, DigestReady published to event bus)
- [x] 4.10 Implement ExtractActionItemsUseCase (LLM extraction → list of ActionItemDTO)
- [x] 4.11 Write tests for ExtractActionItemsUseCase (extraction, empty result)

## 5. Search Application: Use Cases & DTOs

- [x] 5.1 Implement SearchResultDTO
- [x] 5.2 Implement SemanticSearchUseCase (embed query, similarity search, min_score/limit filtering, ordered results)
- [x] 5.3 Write tests for SemanticSearchUseCase (fake embedding + fake vector repo, scoring, limit, no matches)
- [x] 5.4 Implement IndexEmailUseCase (extract text, embed, persist SearchDocument; assert dimension match)
- [x] 5.5 Write tests for IndexEmailUseCase (text extraction, embedding, persistence)
- [x] 5.6 Implement RebuildIndexUseCase (iterate, re-embed, re-index, return statistics)
- [x] 5.7 Write tests for RebuildIndexUseCase (full rebuild, empty index)

## 6. Notification Application: Use Cases

- [x] 6.1 Implement NotifyImportantEmailUseCase (subscribe to ImportantEmailDetected, dispatch via NotificationGateway.send())
- [x] 6.2 Write tests for NotifyImportantEmailUseCase (event handling, dispatch, failure surfaced)
- [x] 6.3 Implement PublishInboxEventUseCase (subscribe to inbox-change events, publish via NotificationGateway.publish(), multi-channel)
- [x] 6.4 Write tests for PublishInboxEventUseCase (event routing, multi-channel publishing)

## 7. Verification

- [x] 7.1 Run full test suite and confirm coverage floors hold (≥90% Domain/, ≥80% overall)
- [x] 7.2 Run ruff and mypy across new application modules and fix findings
