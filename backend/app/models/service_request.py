
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import BigInteger, Integer, Text
from sqlmodel import SQLModel, Field

# Ensure related models are registered in metadata
from app.models.group import Group


class ServiceRequest(SQLModel, table=True):
    __tablename__ = "service_requests"

    id: Optional[int] = Field(
        default=None,
        primary_key=True,
        sa_type=BigInteger().with_variant(Integer, "sqlite"),
    )

    # Student who created the request
    user_id: Optional[UUID] = Field(
        default=None,
        foreign_key="users.id",
        index=True,
    )

    # Staff member assigned to manage the request
    assigned_to: Optional[UUID] = Field(
        default=None,
        foreign_key="users.id",
        index=True,
    )

    # Shared group this request belongs to (None for personal requests)
    group_id: Optional[UUID] = Field(
        default=None,
        foreign_key="groups.id",
        ondelete="RESTRICT",
        index=True,
    )

    title: str = Field(max_length=150)
    description: str = Field(sa_type=Text)
    category: str = Field(max_length=100)
    status: str = Field(default="pending", max_length=30)

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
