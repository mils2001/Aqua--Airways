"""Add per-booking seat allocations

Revision ID: 8bf20c09c54e
Revises: 1065b4741887
Create Date: 2026-11-04

"""
from alembic import op
import sqlalchemy as sa


revision = "8bf20c09c54e"
down_revision = "1065b4741887"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "booking_seats",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("booking_id", sa.Integer(), nullable=False),
        sa.Column("schedule_id", sa.Integer(), nullable=False),
        sa.Column("seat_number", sa.Integer(), nullable=False),
        sa.CheckConstraint("seat_number > 0", name="check_seat_number"),
        sa.ForeignKeyConstraint(["booking_id"], ["bookings.id"]),
        sa.ForeignKeyConstraint(["schedule_id"], ["flight_schedules.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "booking_id",
            "seat_number",
            name="unique_booking_seat"
        ),
        sa.UniqueConstraint(
            "schedule_id",
            "seat_number",
            name="unique_schedule_seat"
        ),
    )


def downgrade():
    op.drop_table("booking_seats")
