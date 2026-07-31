```
gmail-api/
│
├── pyproject.toml
├── gmail-api.iml
├── Dockerfile
├── docker-compose.yml
├── .env
├── .env.example
├── README.md
├── alembic.ini
│
├── specs/
│   │
│   ├── docs/
│   │   ├── architecture.md
│   │   ├── sequence-diagrams.md
│   │   ├── domain-model.md
│   │   └── api.md
│   │   └── project_structure.md
│   │
│   └── guidelines/
│       ├── base.md
│       ├── backend.md
│       ├── testing.md
│       ├── documentation.md
│       └── git-workflow.md
├── tests/
│   ├── unit/
│   └── integration/
│
└── src/
    │
    ├── Bootstrap/
    │   ├── DependencyContainer.py
    │   ├── Logging.py
    │   ├── Lifespan.py
    │   └── Settings.py
    │
    ├── Common/
    │   │
    │   ├── Domain/
    │   │   ├── ValueObjects/
    │   │   ├── Exceptions/
    │   │   ├── Events/
    │   │   ├── Specifications/
    │   │   └── Repository/
    │   │
    │   └── Infrastructure/
    │       ├── Persistence/
    │       │   └── Migrations/ 
    │       ├── Messaging/
    │       ├── LLM/
    │       ├── Clock/
    │       └── IdGenerator/
    │
    ├── Gmail/
    │
    │   ├── Domain/
    │   │   │
    │   │   ├── Entities/
    │   │   │   ├── Email.py
    │   │   │   ├── Thread.py
    │   │   │   ├── Attachment.py
    │   │   │   └── Label.py
    │   │   │
    │   │   ├── ValueObjects/
    │   │   │   ├── EmailAddress.py
    │   │   │   ├── GmailMessageId.py
    │   │   │   ├── HistoryId.py
    │   │   │   ├── ThreadId.py
    │   │   │   └── GmailQuery.py
    │   │   │
    │   │   ├── Repository/
    │   │   │   ├── EmailRepository.py
    │   │   │   └── ThreadRepository.py
    │   │   │
    │   │   ├── Gateway/
    │   │   │   └── GmailGateway.py
    │   │   │
    │   │   ├── Mapper/
    │   │   │   ├── EmailMapper.py
    │   │   │   └── ThreadMapper.py
    │   │   │
    │   │   └── Events/
    │   │       ├── EmailReceived.py
    │   │       └── InboxSynchronized.py
    │   │
    │   ├── Application/
    │   │   │
    │   │   ├── UseCases/
    │   │   │   ├── SynchronizeInboxUseCase.py
    │   │   │   ├── SearchEmailsUseCase.py
    │   │   │   ├── GetThreadUseCase.py
    │   │   │   ├── WatchInboxUseCase.py
    │   │   │   ├── ListUnreadUseCase.py
    │   │   │   └── GetEmailUseCase.py
    │   │   │
    │   │   ├── DTO/
    │   │   ├── Commands/
    │   │   ├── Queries/
    │   │   └── Handlers/
    │   │
    │   └── Infrastructure/
    │       │
    │       ├── Google/
    │       │   ├── GmailApiGateway.py
    │       │   ├── GmailWatcher.py
    │       │   ├── GmailHistorySynchronizer.py
    │       │   └── GmailOAuthProvider.py
    │       │
    │       ├── Persistence/
    │       │   ├── SqlAlchemy/
    │       │   │   ├── Models/
    │       │   │   ├── Repositories/
    │       │   │   └── Mappers/
    │       │   │
    │       │   └── PostgreSQL/
    │       │
    │       └── MCP/
    │
    ├── Intelligence/
    │
    │   ├── Domain/
    │   │   ├── Entities/
    │   │   │   ├── Summary.py
    │   │   │   ├── Suggestion.py
    │   │   │   └── Classification.py
    │   │   │
    │   │   ├── Repository/
    │   │   ├── Gateway/
    │   │   │   └── LlmGateway.py
    │   │   └── ValueObjects/
    │   │
    │   ├── Application/
    │   │   ├── UseCases/
    │   │   │   ├── SummarizeEmailUseCase.py
    │   │   │   ├── SuggestReplyUseCase.py
    │   │   │   ├── DailyDigestUseCase.py
    │   │   │   ├── WeeklyDigestUseCase.py
    │   │   │   ├── ClassifyEmailUseCase.py
    │   │   │   └── ExtractActionItemsUseCase.py
    │   │   └── DTO/
    │   │
    │   └── Infrastructure/
    │       └── LlamaCpp/
    │           └── LlamaCppGateway.py
    │
    ├── Search/
    │
    │   ├── Domain/
    │   │   ├── Repository/
    │   │   ├── Gateway/
    │   │   │   └── EmbeddingGateway.py
    │   │   └── Entities/
    │   │
    │   ├── Application/
    │   │   └── UseCases/
    │   │       ├── SemanticSearchUseCase.py
    │   │       ├── IndexEmailUseCase.py
    │   │       └── RebuildIndexUseCase.py
    │   │
    │   └── Infrastructure/
    │       ├── SqliteVSS/
    │       ├── PgVector/
    │       └── BGE/
    │
    ├── Notification/
    │
    │   ├── Domain/
    │   │   ├── Gateway/
    │   │   │   └── NotificationGateway.py
    │   │   └── Events/
    │   │
    │   ├── Application/
    │   │   └── UseCases/
    │   │       ├── NotifyImportantEmailUseCase.py
    │   │       └── PublishInboxEventUseCase.py
    │   │
    │   └── Infrastructure/
    │       ├── RabbitMQ/
    │       ├── Redis/
    │       └── Webhook/
    │
    └── MCP/
        │
        ├── Server.py
        ├── ToolRegistry.py
        ├── Resources.py
        ├── Prompts.py
        └── Tools/
            ├── SearchEmailsTool.py
            ├── GetThreadTool.py
            ├── DailyDigestTool.py
            ├── SuggestReplyTool.py
            ├── SemanticSearchTool.py
            └── WatchStatusTool.py 
```
