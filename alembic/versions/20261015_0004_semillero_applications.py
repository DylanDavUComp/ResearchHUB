"""Create semillero enrollment workflow tables.

Revision ID: 20261015_0004
Revises: 20261014_0003
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20261015_0004"
down_revision: str | None = "20261014_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "semillero_applications",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("student_id", sa.String(36), nullable=False),
        sa.Column("reviewer_id", sa.String(36), nullable=True),
        sa.Column("create_key", sa.String(100), nullable=False),
        sa.Column("create_hash", sa.String(64), nullable=False),
        sa.Column("semillero_name", sa.String(160), nullable=False),
        sa.Column("project_title", sa.String(220), nullable=False),
        sa.Column("program", sa.String(160), nullable=False),
        sa.Column("current_stage", sa.Integer(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("registration_reference", sa.String(160), nullable=True),
        sa.Column("semester", sa.Integer(), nullable=True),
        sa.Column("plan_summary", sa.Text(), nullable=True),
        sa.Column("plan_deliverables", sa.Text(), nullable=True),
        sa.Column("planned_hours", sa.Integer(), nullable=True),
        sa.Column("plan_status", sa.String(20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["student_id"], ["usuarios.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["reviewer_id"], ["usuarios.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("student_id", "create_key"),
    )
    op.create_index(
        "ix_semillero_applications_student_id", "semillero_applications", ["student_id"]
    )
    op.create_index(
        "ix_semillero_applications_reviewer_id",
        "semillero_applications",
        ["reviewer_id"],
    )
    op.create_table(
        "semillero_events",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("application_id", sa.String(36), nullable=False),
        sa.Column("actor_id", sa.String(36), nullable=False),
        sa.Column("action", sa.String(30), nullable=False),
        sa.Column("from_stage", sa.Integer(), nullable=False),
        sa.Column("to_stage", sa.Integer(), nullable=False),
        sa.Column("comment", sa.String(500), nullable=False),
        sa.Column("idempotency_key", sa.String(100), nullable=False),
        sa.Column("request_hash", sa.String(64), nullable=False),
        sa.Column("result_snapshot", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["application_id"], ["semillero_applications.id"], ondelete="RESTRICT"
        ),
        sa.UniqueConstraint("application_id", "idempotency_key"),
    )
    op.create_index(
        "ix_semillero_events_application_id", "semillero_events", ["application_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_semillero_events_application_id", table_name="semillero_events")
    op.drop_table("semillero_events")
    op.drop_index(
        "ix_semillero_applications_student_id", table_name="semillero_applications"
    )
    op.drop_index(
        "ix_semillero_applications_reviewer_id", table_name="semillero_applications"
    )
    op.drop_table("semillero_applications")
