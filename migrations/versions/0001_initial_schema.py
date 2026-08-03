"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-08-04
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "emails",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("message_id", sa.String(length=255), nullable=False),
        sa.Column("thread_id", sa.String(length=255), nullable=False),
        sa.Column("snippet", sa.Text(), nullable=True),
        sa.Column("subject", sa.Text(), nullable=True),
        sa.Column("from_address", sa.String(length=320), nullable=True),
        sa.Column("to_addresses", sa.JSON(), nullable=True),
        sa.Column("date_sent", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_read", sa.Boolean(), nullable=True),
        sa.Column("labels", sa.JSON(), nullable=True),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column("attachments", sa.JSON(), nullable=True),
        sa.Column("is_trashed", sa.Boolean(), nullable=True),
    )
    op.create_index("ix_emails_message_id", "emails", ["message_id"], unique=True)
    op.create_index("ix_emails_thread_id", "emails", ["thread_id"])

    op.create_table(
        "threads",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("thread_id", sa.String(length=255), nullable=False),
        sa.Column("snippet", sa.Text(), nullable=True),
        sa.Column("subject", sa.Text(), nullable=True),
        sa.Column("participants", sa.JSON(), nullable=True),
        sa.Column("email_entries", sa.JSON(), nullable=True),
        sa.Column("last_updated", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_read", sa.Boolean(), nullable=True),
    )
    op.create_index("ix_threads_thread_id", "threads", ["thread_id"], unique=True)

    op.create_table(
        "attachments",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("file_name", sa.String(length=1024), nullable=True),
        sa.Column("mime_type", sa.String(length=255), nullable=True),
        sa.Column("size_bytes", sa.Integer(), nullable=True),
        sa.Column("attachment_id", sa.String(length=255), nullable=True),
        sa.Column("download_url", sa.Text(), nullable=True),
    )

    op.create_table(
        "labels",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("label_id", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=True),
        sa.Column("color", sa.String(length=64), nullable=True),
        sa.Column("type", sa.String(length=32), nullable=True),
    )
    op.create_index("ix_labels_label_id", "labels", ["label_id"])


def downgrade() -> None:
    op.drop_index("ix_labels_label_id", table_name="labels")
    op.drop_table("labels")
    op.drop_table("attachments")
    op.drop_index("ix_threads_thread_id", table_name="threads")
    op.drop_table("threads")
    op.drop_index("ix_emails_thread_id", table_name="emails")
    op.drop_index("ix_emails_message_id", table_name="emails")
    op.drop_table("emails")
