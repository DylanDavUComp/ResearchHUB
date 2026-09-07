"""create roles and permissions

Revision ID: 20260824_0002
Revises: 20260812_0001
Create Date: 2026-08-24
"""

from collections.abc import Sequence
from uuid import uuid4

import sqlalchemy as sa
from alembic import op


revision: str = "20260824_0002"
down_revision: str | None = "20260812_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
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

    connection = op.get_bind()

    # =========================================================
    # DATOS EXISTENTES
    # =========================================================
    users = connection.execute(
        sa.text(
            """
            SELECT id, role, permissions
            FROM usuarios
            """
        )
    ).mappings().all()

    roles_by_name: dict[str, str] = {}
    permissions_by_code: dict[str, str] = {}
    role_permissions: dict[str, set[str]] = {}

    # =========================================================
    # MIGRAR ROLES EXISTENTES
    # =========================================================
    for user in users:
        role_name = user["role"]

        if role_name not in roles_by_name:
            role_id = str(uuid4())

            role_code = (
                role_name.strip()
                .lower()
                .replace(" ", "_")
                .replace("/", "_")
            )

            connection.execute(
                sa.text(
                    """
                    INSERT INTO roles
                        (id, code, name, description, active)
                    VALUES
                        (:id, :code, :name, :description, true)
                    """
                ),
                {
                    "id": role_id,
                    "code": role_code,
                    "name": role_name,
                    "description": (
                        f"Rol migrado desde usuarios.role: {role_name}"
                    ),
                },
            )

            roles_by_name[role_name] = role_id
            role_permissions[role_name] = set()

    # =========================================================
    # MIGRAR PERMISOS EXISTENTES
    # =========================================================
    for user in users:
        role_name = user["role"]
        permissions = user["permissions"] or []

        for permission_code in permissions:
            permission_code = str(permission_code)

            role_permissions.setdefault(
                role_name,
                set(),
            ).add(permission_code)

            if permission_code not in permissions_by_code:
                permission_id = str(uuid4())

                module = permission_code.split(
                    ":",
                    maxsplit=1,
                )[0]

                permission_name = (
                    permission_code
                    .replace(":", " ")
                    .replace("_", " ")
                    .title()
                )

                connection.execute(
                    sa.text(
                        """
                        INSERT INTO permisos
                            (id, code, name, module, description)
                        VALUES
                            (:id, :code, :name, :module, :description)
                        """
                    ),
                    {
                        "id": permission_id,
                        "code": permission_code,
                        "name": permission_name,
                        "module": module,
                        "description": (
                            "Permiso migrado desde "
                            "usuarios.permissions"
                        ),
                    },
                )

                permissions_by_code[permission_code] = permission_id

    # =========================================================
    # ASIGNAR ROLES A USUARIOS
    # =========================================================
    for user in users:
        role_id = roles_by_name[user["role"]]

        connection.execute(
            sa.text(
                """
                INSERT INTO usuario_roles
                    (user_id, role_id)
                VALUES
                    (:user_id, :role_id)
                ON CONFLICT DO NOTHING
                """
            ),
            {
                "user_id": user["id"],
                "role_id": role_id,
            },
        )

    # =========================================================
    # ASIGNAR PERMISOS A ROLES
    # =========================================================
    for role_name, permission_codes in role_permissions.items():
        role_id = roles_by_name[role_name]

        for permission_code in permission_codes:
            permission_id = permissions_by_code[permission_code]

            connection.execute(
                sa.text(
                    """
                    INSERT INTO rol_permisos
                        (role_id, permission_id)
                    VALUES
                        (:role_id, :permission_id)
                    ON CONFLICT DO NOTHING
                    """
                ),
                {
                    "role_id": role_id,
                    "permission_id": permission_id,
                },
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