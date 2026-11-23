
from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlmodel import SQLModel, Field


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    email: str = Field(max_length=255, unique=True, index=True)
    name: str = Field(max_length=150)
    password_hash: str = Field(max_length=255)
    role: str = Field(default="STUDENT", max_length=20)
    token_version: int = Field(default=0)

    # Account status
    is_active: bool = Field(default=True)

    # Administrative ban information
    is_banned: bool = Field(default=False)
    ban_reason: str | None = Field(default=None, max_length=500)
    banned_at: datetime | None = Field(default=None)
    banned_by: UUID | None = Field(
        default=None,
        foreign_key="users.id",
        ondelete="SET NULL",
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
