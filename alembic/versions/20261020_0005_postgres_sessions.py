"""store sessions and failed logins in PostgreSQL

Revision ID: 20261020_0005
Revises: 20261019_0004
Create Date: 2026-10-20

Replaces stateless browser tokens with server-side sessions. Only HMAC digests of
session tokens and login emails are stored.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20261020_0005"
down_revision: str | None = "20261019_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "sesiones",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("token_digest", sa.String(64), nullable=False),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_reason", sa.String(40), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["usuarios.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_digest", name="uq_sesiones_token_digest"),
    )
    op.create_index("ix_sesiones_user_id", "sesiones", ["user_id"])
    op.create_index("ix_sesiones_expires_at", "sesiones", ["expires_at"])

    op.create_table(
        "intentos_login",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("email_digest", sa.String(64), nullable=False),
        sa.Column("attempted_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_intentos_login_email_digest", "intentos_login", ["email_digest"])
    op.create_index("ix_intentos_login_attempted_at", "intentos_login", ["attempted_at"])


def downgrade() -> None:
    op.drop_index("ix_intentos_login_attempted_at", table_name="intentos_login")
    op.drop_index("ix_intentos_login_email_digest", table_name="intentos_login")
    op.drop_table("intentos_login")
    op.drop_index("ix_sesiones_expires_at", table_name="sesiones")
    op.drop_index("ix_sesiones_user_id", table_name="sesiones")
    op.drop_table("sesiones")
