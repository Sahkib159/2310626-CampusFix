
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

import jwt

from app.auth.config import (
    JWT_SECRET_KEY,
    JWT_ALGORITHM,
    ACCESS_TOKEN_EXPIRE,
)


def create_access_token(user_id: UUID) -> str:
    """
    Generate a signed JWT access token for a user.
    """

    now = datetime.now(timezone.utc)
    expires_at = now + ACCESS_TOKEN_EXPIRE

    payload = {
        "sub": str(user_id),
        "type": "access",
        "iat": now,
        "exp": expires_at,
    }

    return jwt.encode(
        payload,
        JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM,
    )


def decode_access_token(token: str) -> dict[str, Any]:
    """
    Validate and decode a JWT access token.
    """

    payload = jwt.decode(
        token,
        JWT_SECRET_KEY,
        algorithms=[JWT_ALGORITHM],
    )

    if payload.get("type") != "access":
        raise jwt.InvalidTokenError(
            "Invalid token type."
        )

    return payload
