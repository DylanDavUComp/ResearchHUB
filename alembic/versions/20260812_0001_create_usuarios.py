"""create usuarios roles and permissions

Revision ID: 20260812_0001
Revises:
Create Date: 2026-08-12
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260812_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # =========================================================
    # USUARIOS
    # =========================================================
    op.create_table(
        "usuarios",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("role", sa.String(80), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("permissions", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_usuarios_email",
        "usuarios",
        ["email"],
        unique=True,
    )

    # =========================================================
    # ROLES
    # =========================================================
    op.create_table(
        "roles",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("code", sa.String(80), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("description", sa.String(255), nullable=True),
        sa.Column(
            "active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
        sa.UniqueConstraint("name"),
    )

    op.create_index(
        "ix_roles_code",
        "roles",
        ["code"],
        unique=True,
    )

    # =========================================================
    # PERMISOS
    # =========================================================
    op.create_table(
        "permisos",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("code", sa.String(100), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("module", sa.String(80), nullable=False),
        sa.Column("description", sa.String(255), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )

    op.create_index(
        "ix_permisos_code",
        "permisos",
        ["code"],
        unique=True,
    )

    # =========================================================
    # USUARIO -> ROL
    # =========================================================
    op.create_table(
        "usuario_roles",
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("role_id", sa.String(36), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["usuarios.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["role_id"],
            ["roles.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("user_id", "role_id"),
    )

    # =========================================================
    # ROL -> PERMISO
    # =========================================================
    op.create_table(
        "rol_permisos",
        sa.Column("role_id", sa.String(36), nullable=False),
        sa.Column("permission_id", sa.String(36), nullable=False),
        sa.ForeignKeyConstraint(
            ["role_id"],
            ["roles.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["permission_id"],
            ["permisos.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("role_id", "permission_id"),
    )


def downgrade() -> None:
    op.drop_table("rol_permisos")
    op.drop_table("usuario_roles")

    op.drop_index(
        "ix_permisos_code",
        table_name="permisos",
    )
    op.drop_table("permisos")

    op.drop_index(
        "ix_roles_code",
        table_name="roles",
    )
    op.drop_table("roles")

    op.drop_index(
        "ix_usuarios_email",
        table_name="usuarios",
    )
    op.drop_table("usuarios")
