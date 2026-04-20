"""add workout reflections

Revision ID: 9d372a7f4b61
Revises: 41a232a48aed
Create Date: 2026-04-20 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "9d372a7f4b61"
down_revision = "41a232a48aed"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "workout_reflections",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("scheduled_workout_id", sa.Integer(), nullable=False),
        sa.Column("energy", sa.String(length=16), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["scheduled_workout_id"], ["scheduled_workouts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "scheduled_workout_id", name="uq_workout_reflections_user_scheduled"),
    )
    op.create_index(
        op.f("ix_workout_reflections_scheduled_workout_id"),
        "workout_reflections",
        ["scheduled_workout_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_workout_reflections_user_id"),
        "workout_reflections",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_workout_reflections_user_id"), table_name="workout_reflections")
    op.drop_index(op.f("ix_workout_reflections_scheduled_workout_id"), table_name="workout_reflections")
    op.drop_table("workout_reflections")

