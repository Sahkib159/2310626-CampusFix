
"""add login attempt tracking

Revision ID: 9563946f4018
Revises: 167da4147f4a
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "9563946f4018"
down_revision = "167da4147f4a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    if not context_is_offline():
        bind = op.get_bind()
        inspector = sa.inspect(bind)

        if inspector.has_table("login_attempts"):
            existing_indexes = {
                index["name"]
                for index in inspector.get_indexes("login_attempts")
            }

            for column in ("email", "ip_address", "successful", "attempted_at"):
                index_name = f"ix_login_attempts_{column}"
                if index_name not in existing_indexes:
                    op.create_index(
                        index_name,
                        "login_attempts",
                        [column],
                        unique=False,
                    )
            return

    op.create_table(
        "login_attempts",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("ip_address", sa.String(length=45), nullable=False),
        sa.Column(
            "successful",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column(
            "attempted_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    for column in ("email", "ip_address", "successful", "attempted_at"):
        op.create_index(
            f"ix_login_attempts_{column}",
            "login_attempts",
            [column],
            unique=False,
        )


def downgrade() -> None:
    op.drop_table("login_attempts")


def context_is_offline() -> bool:
    from alembic import context
    return context.is_offline_mode()
