
"""add audit log table

Revision ID: c4a91f72d830
Revises: e107d54424dd
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c4a91f72d830"
down_revision: Union[str, None] = "e107d54424dd"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if "audit_logs" not in inspector.get_table_names():
        op.create_table(
            "audit_logs",
            sa.Column("id", sa.Uuid(), nullable=False),
            sa.Column("actor_id", sa.Uuid(), nullable=True),
            sa.Column("target_user_id", sa.Uuid(), nullable=True),
            sa.Column("action", sa.String(length=100), nullable=False),
            sa.Column("email", sa.String(length=255), nullable=True),
            sa.Column(
                "ip_address",
                sa.String(length=45),
                nullable=False,
                server_default="unknown",
            ),
            sa.Column("user_agent", sa.String(length=1000), nullable=True),
            sa.Column("details", sa.Text(), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
            ),
            sa.ForeignKeyConstraint(
                ["actor_id"],
                ["users.id"],
                ondelete="SET NULL",
            ),
            sa.ForeignKeyConstraint(
                ["target_user_id"],
                ["users.id"],
                ondelete="SET NULL",
            ),
            sa.PrimaryKeyConstraint("id"),
        )

    inspector = sa.inspect(bind)
    existing_indexes = {
        index["name"]
        for index in inspector.get_indexes("audit_logs")
    }

    indexes = {
        "ix_audit_logs_actor_id": ["actor_id"],
        "ix_audit_logs_target_user_id": ["target_user_id"],
        "ix_audit_logs_action": ["action"],
        "ix_audit_logs_email": ["email"],
        "ix_audit_logs_created_at": ["created_at"],
    }

    for index_name, columns in indexes.items():
        if index_name not in existing_indexes:
            op.create_index(
                index_name,
                "audit_logs",
                columns,
            )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if "audit_logs" not in inspector.get_table_names():
        return

    existing_indexes = {
        index["name"]
        for index in inspector.get_indexes("audit_logs")
    }

    indexes = [
        "ix_audit_logs_created_at",
        "ix_audit_logs_email",
        "ix_audit_logs_action",
        "ix_audit_logs_target_user_id",
        "ix_audit_logs_actor_id",
    ]

    for index_name in indexes:
        if index_name in existing_indexes:
            op.drop_index(index_name, table_name="audit_logs")

    op.drop_table("audit_logs")
