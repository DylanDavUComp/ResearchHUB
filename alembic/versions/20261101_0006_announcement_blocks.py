"""rich announcement content and uploaded files

Revision ID: 20261101_0006
Revises: 20261020_0005
Create Date: 2026-11-01

Adds block content to announcements (existing plain text becomes paragraphs) and
stores uploaded images and documents in PostgreSQL with size limits (ADR-006).
Additive: no existing column or row is removed.
"""

import re
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20261101_0006"
down_revision: str | None = "20261020_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def paragraphs(text: str | None) -> list[dict[str, object]]:
    return [
        {"type": "paragraph", "runs": [{"text": part.strip()}]}
        for part in re.split(r"\n\s*\n", text or "")
        if part.strip()
    ]


def upgrade() -> None:
    op.add_column("announcements", sa.Column("content", sa.JSON(), nullable=True))
    announcements = sa.table(
        "announcements",
        sa.column("id", sa.String),
        sa.column("body", sa.Text),
        sa.column("content", sa.JSON),
    )
    connection = op.get_bind()
    rows = connection.execute(
        sa.select(announcements.c.id, announcements.c.body)
    ).fetchall()
    for announcement_id, body in rows:
        connection.execute(
            announcements.update()
            .where(announcements.c.id == announcement_id)
            .values(content=paragraphs(body))
        )

    op.create_table(
        "announcement_assets",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("announcement_id", sa.String(36), nullable=True),
        sa.Column("kind", sa.String(20), nullable=False),
        sa.Column("content_type", sa.String(80), nullable=False),
        sa.Column("filename", sa.String(200), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column("data", sa.LargeBinary(), nullable=False),
        sa.Column("uploaded_by", sa.String(36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["announcement_id"], ["announcements.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_announcement_assets_announcement_id",
        "announcement_assets",
        ["announcement_id"],
    )
    op.create_index(
        "ix_announcement_assets_created_at", "announcement_assets", ["created_at"]
    )


def downgrade() -> None:
    op.drop_index("ix_announcement_assets_created_at", "announcement_assets")
    op.drop_index("ix_announcement_assets_announcement_id", "announcement_assets")
    op.drop_table("announcement_assets")
    op.drop_column("announcements", "content")
