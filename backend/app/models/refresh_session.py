
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from sqlmodel import SQLModel, Field


class RefreshSession(SQLModel, table=True):
    __tablename__ = "refresh_sessions"

    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
    )

    user_id: UUID = Field(
        foreign_key="users.id",
        ondelete="CASCADE",
        index=True,
    )

    # Identifies tokens belonging to the same login session.
    family_id: UUID = Field(
        default_factory=uuid4,
        index=True,
    )

    # Store only the hashed refresh token, never the raw token.
    token_hash: str = Field(
        max_length=255,
        unique=True,
        index=True,
    )

    expires_at: datetime

    revoked_at: Optional[datetime] = Field(
        default=None,
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
