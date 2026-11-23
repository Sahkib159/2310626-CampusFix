"""add user token version

Revision ID: 2f6d8a1c4b90
Revises: c4a91f72d830
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "2f6d8a1c4b90"
down_revision: Union[str, Sequence[str], None] = "c4a91f72d830"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "token_version",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
    )


def downgrade() -> None:
    op.drop_column("users", "token_version")
