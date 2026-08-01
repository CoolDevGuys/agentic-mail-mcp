## 1. Gmail Domain: Value Objects

- [x] 1.1 Implement EmailAddress value object with RFC 5322 validation, local_part/domain properties, max 254 chars
- [x] 1.2 Write tests for EmailAddress (valid emails, invalid formats, subdomains, plus addressing, edge cases)
- [x] 1.3 Implement GmailMessageId value object (wraps Gmail string message ID, immutable)
- [x] 1.4 Implement ThreadId value object (wraps Gmail thread ID)
- [x] 1.5 Implement HistoryId value object (wraps Gmail history ID string)
- [x] 1.6 Implement GmailQuery value object with validation and builders (from_sender, with_subject, date_range, has_attachment, label, unread)
- [x] 1.7 Write tests for Gmail-specific value objects (validation, immutability, GmailQuery builders compose correctly)

## 2. Gmail Domain: Aggregates

- [x] 2.1 Implement Email aggregate root with fields, factory from_gmail_message(), behaviors (mark_read, add_label, remove_label, archive, move_to_trash, restore_from_trash), and invariants
- [x] 2.2 Write tests for Email aggregate (factory, all behaviors, invariants, domain event emission)
- [x] 2.3 Implement Thread aggregate with fields, behaviors (add_email, mark_read, add_label, archive, move_to_trash), and invariants
- [x] 2.4 Write tests for Thread aggregate (behaviors, invariants, multi-email thread operations)
- [x] 2.5 Implement Attachment entity with AttachmentMetadata value object
- [x] 2.6 Write tests for Attachment entity and metadata validation
- [x] 2.7 Implement Label entity with rename behavior and system label protection invariant
- [x] 2.8 Write tests for Label entity (creation, rename, system label protection)

## 3. Gmail Domain: Ports, Mappers, Events

- [x] 3.1 Implement EmailRepository protocol (find_by_id, find_by_gmail_message_id, find_by_thread_id, search, list_unread, save, delete)
- [x] 3.2 Implement ThreadRepository protocol (find_by_id, find_by_gmail_thread_id, save, delete)
- [x] 3.3 Write protocol contract tests using fakes for repositories
- [x] 3.4 Implement GmailGateway anti-corruption layer port with all methods and gateway DTOs
- [x] 3.5 Implement EmailMapper.to_domain() and ThreadMapper.to_domain()
- [x] 3.6 Write tests for mappers with sample Gmail API responses
- [x] 3.7 Implement Gmail domain events (EmailReceived, EmailArchived, EmailDeleted, EmailForwarded, EmailLabeled, InboxSynchronized)
- [x] 3.8 Write tests for domain event instantiation and required fields

## 4. Intelligence Domain

- [x] 4.1 Implement Summary entity with validation
- [x] 4.2 Implement Classification entity with category/priority/confidence validation
- [x] 4.3 Implement Suggestion entity with suggestion_type validation
- [x] 4.4 Write tests for all Intelligence entities (creation, field validation)
- [x] 4.5 Implement PromptTemplate value object with render(**kwargs) method
- [x] 4.6 Implement ModelConfig value object with validation
- [x] 4.7 Write tests for PromptTemplate rendering and ModelConfig validation
- [x] 4.8 Implement LlmGateway port with LlmResponse DTO

## 5. Search Domain

- [x] 5.1 Implement SearchDocument entity with embedding vector support
- [x] 5.2 Write tests for SearchDocument entity creation
- [x] 5.3 Implement EmbeddingGateway port with embed() and dimension() methods
- [x] 5.4 Implement VectorSearchRepository protocol with SearchResult DTO
- [x] 5.5 Write protocol contract tests for VectorSearchRepository using fake

## 6. Notification Domain

- [x] 6.1 Implement ImportantEmailDetected domain event
- [x] 6.2 Implement InboxChanged domain event
- [x] 6.3 Implement DigestReady domain event
- [x] 6.4 Write tests for all Notification domain events
- [x] 6.5 Implement NotificationGateway port with send() and publish() methods
