
"""add user ban management fields

Revision ID: e107d54424dd
Revises: b2c8a1e94d10
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e107d54424dd"
down_revision: Union[str, Sequence[str], None] = "b2c8a1e94d10"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add ban status. Existing users receive False.
    op.add_column(
        "users",
        sa.Column(
            "is_banned",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )

    op.add_column(
        "users",
        sa.Column("ban_reason", sa.String(length=500), nullable=True),
    )

    op.add_column(
        "users",
        sa.Column(
            "banned_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )

    op.add_column(
        "users",
        sa.Column("banned_by", sa.Uuid(), nullable=True),
    )

    op.create_foreign_key(
        "fk_users_banned_by_users",
        "users",
        "users",
        ["banned_by"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_users_banned_by_users",
        "users",
        type_="foreignkey",
    )

    op.drop_column("users", "banned_by")
    op.drop_column("users", "banned_at")
    op.drop_column("users", "ban_reason")
    op.drop_column("users", "is_banned")
