
from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlmodel import SQLModel, Field


class AuditLog(SQLModel, table=True):
    __tablename__ = "audit_logs"

    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
    )

    # The user who performed the action.
    # NULL is allowed for anonymous actions, such as failed login attempts.
    actor_id: UUID | None = Field(
        default=None,
        foreign_key="users.id",
        ondelete="SET NULL",
        index=True,
    )

    # The user affected by the action.
    target_user_id: UUID | None = Field(
        default=None,
        foreign_key="users.id",
        ondelete="SET NULL",
        index=True,
    )

    # Examples: LOGIN_SUCCESS, LOGIN_FAILED, USER_BANNED
    action: str = Field(
        max_length=100,
        index=True,
    )

    # Useful when the action concerns an email but no user was identified.
    email: str | None = Field(
        default=None,
        max_length=255,
        index=True,
    )

    ip_address: str = Field(
        default="unknown",
        max_length=45,
    )

    user_agent: str | None = Field(
        default=None,
        max_length=1000,
    )

    # Additional information about the event.
    # Never store passwords, access tokens or refresh tokens here.
    details: str | None = Field(default=None)

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        index=True,
    )
