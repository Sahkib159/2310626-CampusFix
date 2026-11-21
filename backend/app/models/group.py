from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import Text, UniqueConstraint
from sqlmodel import SQLModel, Field


class Group(SQLModel, table=True):
    __tablename__ = "groups"

    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
    )
    name: str = Field(
        max_length=100,
        index=True,
    )
    description: Optional[str] = Field(
        default=None,
        sa_type=Text,
    )
    # Group owner: authoritative source of truth for group ownership.
    owner_id: UUID = Field(
        foreign_key="users.id",
        ondelete="RESTRICT",
        index=True,
    )
    # Archived groups are read-only; all mutation operations are blocked.
    is_archived: bool = Field(
        default=False,
        index=True,
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )


class GroupMember(SQLModel, table=True):
    __tablename__ = "group_members"
    __table_args__ = (
        UniqueConstraint(
            "group_id",
            "user_id",
            name="uq_group_members_group_user",
        ),
    )

    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
    )
    group_id: UUID = Field(
        foreign_key="groups.id",
        ondelete="CASCADE",
        index=True,
    )
    user_id: UUID = Field(
        foreign_key="users.id",
        ondelete="CASCADE",
        index=True,
    )

    # Fine-grained member permissions: deny by default.
    can_create_requests: bool = Field(default=False)
    can_edit_requests: bool = Field(default=False)
    can_assign_requests: bool = Field(default=False)

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )
