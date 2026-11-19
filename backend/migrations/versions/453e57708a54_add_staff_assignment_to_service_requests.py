
"""add staff assignment to service requests

Revision ID: 453e57708a54
Revises: e4620a8de715
Create Date: 2026-11-19 10:47:37.313350
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "453e57708a54"
down_revision: Union[str, Sequence[str], None] = "e4620a8de715"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "service_requests",
        sa.Column("assigned_to", sa.Uuid(), nullable=True),
    )

    op.create_index(
        "ix_service_requests_assigned_to",
        "service_requests",
        ["assigned_to"],
        unique=False,
    )

    op.create_foreign_key(
        "fk_service_requests_assigned_to_users",
        "service_requests",
        "users",
        ["assigned_to"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_service_requests_assigned_to_users",
        "service_requests",
        type_="foreignkey",
    )

    op.drop_index(
        "ix_service_requests_assigned_to",
        table_name="service_requests",
    )

    op.drop_column("service_requests", "assigned_to")
