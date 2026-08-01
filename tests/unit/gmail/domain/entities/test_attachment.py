from __future__ import annotations

import pytest

from src.Common.Domain.Exceptions import ValidationError
from src.Common.Domain.ValueObjects.uuid_id import UUIDId
from src.Gmail.Domain.Entities.attachment import Attachment, AttachmentMetadata


class TestAttachmentCreation:
    def test_valid_creation(self) -> None:
        attachment = Attachment(
            id=UUIDId.generate(),
            file_name="document.pdf",
            mime_type="application/pdf",
            size_bytes=1024,
            attachment_id="att_123",
        )

        assert attachment.file_name == "document.pdf"
        assert attachment.mime_type == "application/pdf"
        assert attachment.size_bytes == 1024
        assert attachment.attachment_id == "att_123"
        assert attachment.download_url == ""

    def test_creation_with_download_url(self) -> None:
        attachment = Attachment(
            id=UUIDId.generate(),
            file_name="image.png",
            mime_type="image/png",
            size_bytes=2048,
            attachment_id="att_456",
            download_url="https://example.com/download",
        )

        assert attachment.download_url == "https://example.com/download"


class TestAttachmentMetadata:
    def test_valid_metadata(self) -> None:
        meta = AttachmentMetadata(
            name="file.txt",
            mime_type="text/plain",
            size_bytes=512,
        )

        assert meta.name == "file.txt"
        assert meta.mime_type == "text/plain"
        assert meta.size_bytes == 512

    def test_negative_size_rejected(self) -> None:
        with pytest.raises(ValidationError, match="size_bytes must be non-negative"):
            AttachmentMetadata(
                name="file.txt",
                mime_type="text/plain",
                size_bytes=-1,
            )

    def test_empty_name_rejected(self) -> None:
        with pytest.raises(ValidationError, match="name must not be empty"):
            AttachmentMetadata(
                name="",
                mime_type="text/plain",
                size_bytes=100,
            )

    def test_equality_same_values(self) -> None:
        m1 = AttachmentMetadata(name="a.txt", mime_type="text/plain", size_bytes=100)
        m2 = AttachmentMetadata(name="a.txt", mime_type="text/plain", size_bytes=100)
        assert m1 == m2

    def test_inequality_different_values(self) -> None:
        m1 = AttachmentMetadata(name="a.txt", mime_type="text/plain", size_bytes=100)
        m2 = AttachmentMetadata(name="b.txt", mime_type="text/plain", size_bytes=100)
        assert m1 != m2

    def test_hash_consistency(self) -> None:
        m1 = AttachmentMetadata(name="a.txt", mime_type="text/plain", size_bytes=100)
        m2 = AttachmentMetadata(name="a.txt", mime_type="text/plain", size_bytes=100)
        assert hash(m1) == hash(m2)

    def test_usable_in_set(self) -> None:
        meta = AttachmentMetadata(name="a.txt", mime_type="text/plain", size_bytes=100)
        s = {meta, meta}
        assert len(s) == 1
