"""create launcher announcements tables

Revision ID: 20261014_0003
Revises: 20260907_0002
Create Date: 2026-10-14
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20261014_0003"
down_revision: str | None = "20260907_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "announcements",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("category", sa.String(20), nullable=False),
        sa.Column("title", sa.String(160), nullable=False),
        sa.Column("summary", sa.String(280), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("link_url", sa.String(500), nullable=True),
        sa.Column("image_url", sa.String(500), nullable=True),
        sa.Column("image_alt", sa.String(200), nullable=True),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("author_id", sa.String(36), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["author_id"], ["usuarios.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_announcements_category", "announcements", ["category"])
    op.create_index("ix_announcements_status", "announcements", ["status"])
    op.create_index("ix_announcements_published_at", "announcements", ["published_at"])

    op.create_table(
        "announcement_audit_events",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("announcement_id", sa.String(36), nullable=False),
        sa.Column("actor_id", sa.String(36), nullable=False),
        sa.Column("actor_role", sa.String(80), nullable=False),
        sa.Column("action", sa.String(20), nullable=False),
        sa.Column("from_status", sa.String(20), nullable=False),
        sa.Column("to_status", sa.String(20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_announcement_audit_events_announcement_id",
        "announcement_audit_events",
        ["announcement_id"],
    )
    op.create_index(
        "ix_announcement_audit_events_actor_id",
        "announcement_audit_events",
        ["actor_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_announcement_audit_events_actor_id",
        table_name="announcement_audit_events",
    )
    op.drop_index(
        "ix_announcement_audit_events_announcement_id",
        table_name="announcement_audit_events",
    )
    op.drop_table("announcement_audit_events")

    op.drop_index("ix_announcements_published_at", table_name="announcements")
    op.drop_index("ix_announcements_status", table_name="announcements")
    op.drop_index("ix_announcements_category", table_name="announcements")
    op.drop_table("announcements")
