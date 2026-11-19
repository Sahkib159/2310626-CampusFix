
"""add service request ownership

Revision ID: e4620a8de715
Revises: 8af42c02f938
Create Date: 2026-11-19 09:56:00.546096

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e4620a8de715"
down_revision: Union[str, Sequence[str], None] = "8af42c02f938"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "service_requests",
        sa.Column("user_id", sa.Uuid(), nullable=True),
    )

    op.create_index(
        "ix_service_requests_user_id",
        "service_requests",
        ["user_id"],
        unique=False,
    )

    op.create_foreign_key(
        "fk_service_requests_user_id_users",
        "service_requests",
        "users",
        ["user_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_service_requests_user_id_users",
        "service_requests",
        type_="foreignkey",
    )

    op.drop_index(
        "ix_service_requests_user_id",
        table_name="service_requests",
    )

    op.drop_column("service_requests", "user_id")
