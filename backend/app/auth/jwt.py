
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

import jwt

from app.auth.config import (
    JWT_SECRET_KEY,
    JWT_ALGORITHM,
    ACCESS_TOKEN_EXPIRE,
)


def create_access_token(user_id: UUID, role: str) -> str:
    """
    Generate a signed JWT access token containing user ID and role.
    """

    now = datetime.now(timezone.utc)
    expires_at = now + ACCESS_TOKEN_EXPIRE

    payload = {
        "sub": str(user_id),
        "role": role,
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

    if not payload.get("sub"):
        raise jwt.InvalidTokenError(
            "Token is missing the user ID."
        )

    if not payload.get("role"):
        raise jwt.InvalidTokenError(
            "Token is missing the user role."
        )

    return payload
