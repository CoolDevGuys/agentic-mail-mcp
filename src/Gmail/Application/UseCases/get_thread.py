from __future__ import annotations

from src.Common.Domain.Exceptions import NotFoundError
from src.Gmail.Application.DTO.dtos import ThreadDTO
from src.Gmail.Application.Queries.queries import GetThreadQuery
from src.Gmail.Domain.Repository.thread_repository import ThreadRepository


class GetThreadUseCase:
    """Resolve a thread and its ordered email IDs into a ThreadDTO."""

    def __init__(self, repository: ThreadRepository) -> None:
        self._repository = repository

    def execute(self, query: GetThreadQuery) -> ThreadDTO:
        thread = self._repository.find_by_gmail_thread_id(query.value)
        if thread is None:
            raise NotFoundError(f"Thread not found: {query.value}")
        return ThreadDTO.from_entity(thread)
