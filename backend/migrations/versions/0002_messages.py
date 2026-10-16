"""Client <-> freelancer chat (messages table).

Revision ID: 0002_messages
Revises: 0001_baseline
Create Date: 2026-10-16
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002_messages"
down_revision: Union[str, None] = "0001_baseline"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 0001 runs create_all from the *current* models, so on a fresh DB the
    # table already exists by the time we get here.
    if sa.inspect(op.get_bind()).has_table("messages"):
        return
    op.create_table(
        "messages",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column("match_id", sa.String(32), sa.ForeignKey("matches.id"), nullable=False),
        sa.Column("sender_id", sa.String(32), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("flagged", sa.Boolean(), nullable=True),
        sa.Column("flag_reasons", sa.JSON(), nullable=True),
        sa.Column("translations", sa.JSON(), nullable=True),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_messages_match_id", "messages", ["match_id"])
    op.create_index("ix_messages_sender_id", "messages", ["sender_id"])
    op.create_index("ix_messages_created_at", "messages", ["created_at"])


def downgrade() -> None:
    op.drop_table("messages")
