
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

    # Account status: inactive accounts cannot authenticate.
    is_active: bool = Field(default=True)

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
