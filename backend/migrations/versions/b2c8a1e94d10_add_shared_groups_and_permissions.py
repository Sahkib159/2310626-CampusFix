
"""add shared groups and fine-grained member permissions

Revision ID: b2c8a1e94d10
Revises: 9563946f4018
Create Date: 2026-11-21 23:45:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# Revision identifiers.
revision: str = "b2c8a1e94d10"
down_revision: Union[str, Sequence[str], None] = "9563946f4018"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()

    def get_inspector():
        return inspect(bind)

    def table_exists(table_name: str) -> bool:
        return table_name in get_inspector().get_table_names()

    def column_exists(table_name: str, column_name: str) -> bool:
        return any(
            column["name"] == column_name
            for column in get_inspector().get_columns(table_name)
        )

    def index_exists(table_name: str, columns: list[str]) -> bool:
        return any(
            index["column_names"] == columns
            for index in get_inspector().get_indexes(table_name)
        )

    def foreign_key_exists(
        table_name: str,
        local_columns: list[str],
        remote_table: str,
        remote_columns: list[str],
    ) -> bool:
        return any(
            fk["constrained_columns"] == local_columns
            and fk["referred_table"] == remote_table
            and fk["referred_columns"] == remote_columns
            for fk in get_inspector().get_foreign_keys(table_name)
        )

    def unique_exists(table_name: str, columns: list[str]) -> bool:
        return any(
            constraint["column_names"] == columns
            for constraint in get_inspector().get_unique_constraints(table_name)
        )

    def ensure_false_default(table_name: str, column_name: str) -> None:
        for column in get_inspector().get_columns(table_name):
            if column["name"] == column_name:
                default = str(column["default"] or "").lower()
                if "false" not in default and default not in {"0", "'0'"}:
                    op.alter_column(
                        table_name,
                        column_name,
                        existing_type=sa.Boolean(),
                        existing_nullable=column["nullable"],
                        server_default=sa.text("false"),
                    )
                return

    # 1. Ensure groups table exists.
    if not table_exists("groups"):
        op.create_table(
            "groups",
            sa.Column("id", sa.Uuid(), nullable=False),
            sa.Column("name", sa.String(100), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("owner_id", sa.Uuid(), nullable=False),
            sa.Column(
                "is_archived",
                sa.Boolean(),
                server_default=sa.text("false"),
                nullable=False,
            ),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(
                ["owner_id"],
                ["users.id"],
                name="fk_groups_owner_id_users",
                ondelete="RESTRICT",
            ),
            sa.PrimaryKeyConstraint("id", name="pk_groups"),
        )
    else:
        ensure_false_default("groups", "is_archived")

        if not foreign_key_exists("groups", ["owner_id"], "users", ["id"]):
            op.create_foreign_key(
                "fk_groups_owner_id_users",
                "groups",
                "users",
                ["owner_id"],
                ["id"],
                ondelete="RESTRICT",
            )

    for column in ["owner_id", "name", "is_archived"]:
        if not index_exists("groups", [column]):
            op.create_index(
                f"ix_groups_{column}",
                "groups",
                [column],
                unique=False,
            )

    # 2. Ensure group_members table exists.
    if not table_exists("group_members"):
        op.create_table(
            "group_members",
            sa.Column("id", sa.Uuid(), nullable=False),
            sa.Column("group_id", sa.Uuid(), nullable=False),
            sa.Column("user_id", sa.Uuid(), nullable=False),
            sa.Column(
                "can_create_requests",
                sa.Boolean(),
                server_default=sa.text("false"),
                nullable=False,
            ),
            sa.Column(
                "can_edit_requests",
                sa.Boolean(),
                server_default=sa.text("false"),
                nullable=False,
            ),
            sa.Column(
                "can_assign_requests",
                sa.Boolean(),
                server_default=sa.text("false"),
                nullable=False,
            ),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(
                ["group_id"],
                ["groups.id"],
                name="fk_group_members_group_id_groups",
                ondelete="CASCADE",
            ),
            sa.ForeignKeyConstraint(
                ["user_id"],
                ["users.id"],
                name="fk_group_members_user_id_users",
                ondelete="CASCADE",
            ),
            sa.PrimaryKeyConstraint("id", name="pk_group_members"),
            sa.UniqueConstraint(
                "group_id",
                "user_id",
                name="uq_group_members_group_user",
            ),
        )
    else:
        for column in [
            "can_create_requests",
            "can_edit_requests",
            "can_assign_requests",
        ]:
            ensure_false_default("group_members", column)

        if not foreign_key_exists(
            "group_members", ["group_id"], "groups", ["id"]
        ):
            op.create_foreign_key(
                "fk_group_members_group_id_groups",
                "group_members",
                "groups",
                ["group_id"],
                ["id"],
                ondelete="CASCADE",
            )

        if not foreign_key_exists(
            "group_members", ["user_id"], "users", ["id"]
        ):
            op.create_foreign_key(
                "fk_group_members_user_id_users",
                "group_members",
                "users",
                ["user_id"],
                ["id"],
                ondelete="CASCADE",
            )

        if not unique_exists("group_members", ["group_id", "user_id"]):
            op.create_unique_constraint(
                "uq_group_members_group_user",
                "group_members",
                ["group_id", "user_id"],
            )

    if not index_exists("group_members", ["group_id"]):
        op.create_index(
            "ix_group_members_group_id",
            "group_members",
            ["group_id"],
            unique=False,
        )

    if not index_exists("group_members", ["user_id"]):
        op.create_index(
            "ix_group_members_user_id",
            "group_members",
            ["user_id"],
            unique=False,
        )

    # 3. Add nullable group_id to existing service requests.
    if not column_exists("service_requests", "group_id"):
        op.add_column(
            "service_requests",
            sa.Column("group_id", sa.Uuid(), nullable=True),
        )

    if not index_exists("service_requests", ["group_id"]):
        op.create_index(
            "ix_service_requests_group_id",
            "service_requests",
            ["group_id"],
            unique=False,
        )

    if not foreign_key_exists(
        "service_requests",
        ["group_id"],
        "groups",
        ["id"],
    ):
        op.create_foreign_key(
            "fk_service_requests_group_id_groups",
            "service_requests",
            "groups",
            ["group_id"],
            ["id"],
            ondelete="RESTRICT",
        )


def downgrade() -> None:
    # Intentionally irreversible. Preserve pre-existing group tables
    # and all group-request associations and related database objects.
    pass
