
from datetime import datetime, timezone
from uuid import UUID

from sqlmodel import Session

from app.models.user import User
from app.models.refresh_session import RefreshSession
from app.auth import repository
from app.auth import schemas
from app.auth.config import REFRESH_TOKEN_EXPIRE
from app.auth.password import hash_password, verify_password
from app.auth.jwt import create_access_token
from app.auth.tokens import (
    generate_refresh_token,
    hash_refresh_token,
)


def _build_token_response(user: User) -> schemas.TokenResponse:
    return schemas.TokenResponse(
        access_token=create_access_token(user.id),
        user=schemas.UserResponse(
            id=str(user.id),
            name=user.name,
            email=user.email,
            role=user.role,
        ),
    )


def _create_refresh_session(
    session: Session,
    user: User,
    family_id: UUID | None = None,
) -> str:
    raw_token = generate_refresh_token()

    refresh_session = RefreshSession(
        user_id=user.id,
        family_id=family_id or UUID(int=0),
        token_hash=hash_refresh_token(raw_token),
        expires_at=datetime.now(timezone.utc) + REFRESH_TOKEN_EXPIRE,
    )

    session.add(refresh_session)
    session.flush()

    if family_id is None:
        refresh_session.family_id = refresh_session.id

    session.commit()

    return raw_token


def signup(
    session: Session,
    data: schemas.SignupRequest,
) -> dict:
    existing_user = repository.get_user_by_email(
        session,
        data.email,
    )

    if existing_user is not None:
        raise ValueError("An account with this email already exists.")

    user = User(
        name=data.name,
        email=data.email,
        password_hash=hash_password(data.password),
        role="STUDENT",
    )

    user = repository.create_user(session, user)

    refresh_token = _create_refresh_session(session, user)

    return {
        "response": _build_token_response(user),
        "refresh_token": refresh_token,
    }


def login(
    session: Session,
    data: schemas.LoginRequest,
) -> dict:
    user = repository.get_user_by_email(
        session,
        data.email,
    )

    if user is None or not verify_password(
        data.password,
        user.password_hash,
    ):
        raise ValueError("Incorrect email or password.")

    refresh_token = _create_refresh_session(session, user)

    return {
        "response": _build_token_response(user),
        "refresh_token": refresh_token,
    }


def refresh_session(
    session: Session,
    raw_token: str,
) -> dict:
    token_hash = hash_refresh_token(raw_token)

    stored_session = repository.get_refresh_session_by_hash(
        session,
        token_hash,
    )

    if stored_session is None:
        raise ValueError("Invalid refresh token.")

    if stored_session.revoked_at is not None:
        repository.revoke_refresh_family(
            session,
            stored_session.family_id,
        )
        raise ValueError("Refresh token has been revoked.")

    now = datetime.now(timezone.utc)

    expires_at = stored_session.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if expires_at <= now:
        repository.revoke_refresh_session(session, stored_session)
        raise ValueError("Refresh token has expired.")

    user = repository.get_user_by_id(
        session,
        stored_session.user_id,
    )

    if user is None:
        raise ValueError("User account not found.")

    family_id = stored_session.family_id

    repository.revoke_refresh_session(session, stored_session)

    new_refresh_token = _create_refresh_session(
        session,
        user,
        family_id,
    )

    return {
        "response": _build_token_response(user),
        "refresh_token": new_refresh_token,
    }


def logout(
    session: Session,
    raw_token: str,
) -> None:
    stored_session = repository.get_refresh_session_by_hash(
        session,
        hash_refresh_token(raw_token),
    )

    if stored_session is not None and stored_session.revoked_at is None:
        repository.revoke_refresh_session(session, stored_session)


def get_user_sessions(
    session: Session,
    user_id: UUID,
) -> list[dict]:
    sessions = repository.get_user_sessions(session, user_id)

    return [
        {
            "id": str(item.id),
            "created_at": item.created_at,
            "expires_at": item.expires_at,
            "revoked": item.revoked_at is not None,
        }
        for item in sessions
    ]


def revoke_user_session(
    session: Session,
    user_id: UUID,
    session_id: str,
) -> dict:
    try:
        parsed_session_id = UUID(session_id)
    except ValueError:
        raise ValueError("Invalid session ID.")

    revoked = repository.revoke_user_session(
        session,
        user_id,
        parsed_session_id,
    )

    if not revoked:
        raise ValueError("Session not found.")

    return {"message": "Session revoked successfully."}
