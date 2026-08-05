"""Create chat sessions and messages.

Revision ID: 0003_create_chat_sessions
Revises: 0002_create_documents
Create Date: 2026-08-06
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0003_create_chat_sessions"
down_revision: Union[str, None] = "0002_create_documents"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create chat session and message tables."""
    op.create_table(
        "chat_sessions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_chat_sessions_user_id",
        "chat_sessions",
        ["user_id"],
        unique=False,
    )

    op.create_table(
        "chat_messages",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["session_id"],
            ["chat_sessions.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "role IN ('user', 'assistant')",
            name="ck_chat_messages_role",
        ),
    )
    op.create_index(
        "ix_chat_messages_session_id",
        "chat_messages",
        ["session_id"],
        unique=False,
    )


def downgrade() -> None:
    """Drop chat messages and sessions."""
    op.drop_index("ix_chat_messages_session_id", table_name="chat_messages")
    op.drop_table("chat_messages")
    op.drop_index("ix_chat_sessions_user_id", table_name="chat_sessions")
    op.drop_table("chat_sessions")
