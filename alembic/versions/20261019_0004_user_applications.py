"""create per-application user access

Revision ID: 20261019_0004
Revises: 20261014_0003
Create Date: 2026-10-19

Existing users keep ResearchHUB, the only application they could use before this
revision. ResearchOS access is never granted implicitly; an administrator assigns it.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20261019_0004"
down_revision: str | None = "20261014_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "usuario_aplicaciones",
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("application", sa.String(40), nullable=False),
        sa.Column("granted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("granted_by_id", sa.String(36), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["usuarios.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["granted_by_id"], ["usuarios.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("user_id", "application"),
        sa.CheckConstraint(
            "application IN ('research_hub', 'research_os')",
            name="ck_usuario_aplicaciones_application",
        ),
    )
    op.create_index(
        "ix_usuario_aplicaciones_application",
        "usuario_aplicaciones",
        ["application"],
    )
    op.execute(
        sa.text(
            "INSERT INTO usuario_aplicaciones (user_id, application, granted_at) "
            "SELECT id, 'research_hub', CURRENT_TIMESTAMP FROM usuarios"
        )
    )


def downgrade() -> None:
    op.drop_index(
        "ix_usuario_aplicaciones_application",
        table_name="usuario_aplicaciones",
    )
    op.drop_table("usuario_aplicaciones")
