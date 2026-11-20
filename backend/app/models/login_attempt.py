
from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlmodel import SQLModel, Field


class LoginAttempt(SQLModel, table=True):
    __tablename__ = "login_attempts"

    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
    )

    # Normalized email entered during login.
    email: str = Field(
        max_length=255,
        index=True,
    )

    # Client IP address used for rate-limit tracking.
    ip_address: str = Field(
        max_length=45,
        index=True,
    )

    # True for successful login, False for failed login.
    successful: bool = Field(
        default=False,
        index=True,
    )

    attempted_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        index=True,
    )
