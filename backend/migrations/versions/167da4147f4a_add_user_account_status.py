
"""add user account status

Revision ID: 167da4147f4a
Revises: 453e57708a54
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "167da4147f4a"
down_revision: Union[str, Sequence[str], None] = "453e57708a54"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
    )


def downgrade() -> None:
    op.drop_column("users", "is_active")
