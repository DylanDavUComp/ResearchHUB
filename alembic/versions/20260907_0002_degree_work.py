"""create configurable degree work tables

Revision ID: 20260907_0002
Revises: 20260812_0001
Create Date: 2026-09-07
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260907_0002"
down_revision: str | None = "20260812_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "degree_work_modalities",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("code", sa.String(80), nullable=False),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("is_homologatable", sa.Boolean(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("initial_semester", sa.Integer(), nullable=True),
        sa.Column("duration_label", sa.String(120), nullable=False),
        sa.Column("min_participants", sa.Integer(), nullable=False),
        sa.Column("max_participants", sa.Integer(), nullable=False),
        sa.Column("requirements", sa.JSON(), nullable=False),
        sa.Column("evaluation_criteria", sa.JSON(), nullable=False),
        sa.Column("workflow_steps", sa.JSON(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index(
        "ix_degree_work_modalities_code",
        "degree_work_modalities",
        ["code"],
        unique=True,
    )
    op.create_index(
        "ix_degree_work_modalities_status",
        "degree_work_modalities",
        ["status"],
    )

    op.create_table(
        "degree_work_cases",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("student_id", sa.String(36), nullable=False),
        sa.Column("modality_id", sa.String(36), nullable=False),
        sa.Column("modality_code", sa.String(80), nullable=False),
        sa.Column("modality_name", sa.String(160), nullable=False),
        sa.Column("modality_version", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(220), nullable=False),
        sa.Column("program", sa.String(160), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("current_step_index", sa.Integer(), nullable=False),
        sa.Column("workflow_snapshot", sa.JSON(), nullable=False),
        sa.Column("assigned_teacher_id", sa.String(36), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["student_id"], ["usuarios.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["assigned_teacher_id"], ["usuarios.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["modality_id"], ["degree_work_modalities.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_degree_work_cases_student_id", "degree_work_cases", ["student_id"]
    )
    op.create_index(
        "ix_degree_work_cases_modality_code", "degree_work_cases", ["modality_code"]
    )
    op.create_index("ix_degree_work_cases_program", "degree_work_cases", ["program"])
    op.create_index("ix_degree_work_cases_status", "degree_work_cases", ["status"])

    op.create_table(
        "degree_work_audit_events",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("case_id", sa.String(36), nullable=False),
        sa.Column("actor_id", sa.String(36), nullable=False),
        sa.Column("actor_role", sa.String(80), nullable=False),
        sa.Column("action", sa.String(30), nullable=False),
        sa.Column("step_code", sa.String(80), nullable=False),
        sa.Column("from_status", sa.String(30), nullable=False),
        sa.Column("to_status", sa.String(30), nullable=False),
        sa.Column("comment", sa.String(500), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["case_id"], ["degree_work_cases.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_degree_work_audit_events_case_id",
        "degree_work_audit_events",
        ["case_id"],
    )
    op.create_index(
        "ix_degree_work_audit_events_actor_id",
        "degree_work_audit_events",
        ["actor_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_degree_work_audit_events_actor_id",
        table_name="degree_work_audit_events",
    )
    op.drop_index(
        "ix_degree_work_audit_events_case_id",
        table_name="degree_work_audit_events",
    )
    op.drop_table("degree_work_audit_events")

    op.drop_index("ix_degree_work_cases_status", table_name="degree_work_cases")
    op.drop_index("ix_degree_work_cases_program", table_name="degree_work_cases")
    op.drop_index(
        "ix_degree_work_cases_modality_code", table_name="degree_work_cases"
    )
    op.drop_index(
        "ix_degree_work_cases_student_id", table_name="degree_work_cases"
    )
    op.drop_table("degree_work_cases")

    op.drop_index(
        "ix_degree_work_modalities_status", table_name="degree_work_modalities"
    )
    op.drop_index(
        "ix_degree_work_modalities_code", table_name="degree_work_modalities"
    )
    op.drop_table("degree_work_modalities")
