
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlmodel import Session

from app.models.user import User
from app.models.refresh_session import RefreshSession
from app.auth import repository
from app.auth import schemas
from app.auth.config import REFRESH_TOKEN_EXPIRE
from app.auth.password import (
    hash_password,
    verify_password,
    needs_password_upgrade,
)
from app.auth.jwt import create_access_token
from app.auth.tokens import (
    generate_refresh_token,
    hash_refresh_token,
)
from app.auth.normalization import normalize_email


# Login rate-limit configuration
LOGIN_ATTEMPT_WINDOW_MINUTES = 15
MAX_FAILED_ATTEMPTS_PER_EMAIL = 5
MAX_FAILED_ATTEMPTS_PER_IP = 20


class LoginRateLimitError(ValueError):
    """Raised when a login rate limit has been reached."""


def _build_token_response(user: User) -> schemas.TokenResponse:
    return schemas.TokenResponse(
        access_token=create_access_token(
            user.id,
            user.role,
            user.token_version,
        ),
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
    commit: bool = True,
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

    if commit:
        session.commit()

    return raw_token


def signup(
    session: Session,
    data: schemas.SignupRequest,
) -> dict:
    email = normalize_email(str(data.email))

    existing_user = repository.get_user_by_email(
        session,
        email,
    )

    if existing_user is not None:
        raise ValueError("An account with this email already exists.")

    user = User(
        name=data.name,
        email=email,
        password_hash=hash_password(data.password),
        role="STUDENT",
        is_active=True,
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
    ip_address: str,
) -> dict:
    email = normalize_email(str(data.email))
    now = datetime.now(timezone.utc)

    window_start = now - timedelta(
        minutes=LOGIN_ATTEMPT_WINDOW_MINUTES
    )

    # Check email-based rate limit.
    email_failures = (
        repository.count_failed_login_attempts_by_email(
            session,
            email,
            window_start,
        )
    )

    # Check IP-based rate limit.
    ip_failures = (
        repository.count_failed_login_attempts_by_ip(
            session,
            ip_address,
            window_start,
        )
    )

    if (
        email_failures >= MAX_FAILED_ATTEMPTS_PER_EMAIL
        or ip_failures >= MAX_FAILED_ATTEMPTS_PER_IP
    ):
        raise LoginRateLimitError(
            "Too many login attempts. Please try again later."
        )

    user = repository.get_user_by_email(
        session,
        email,
    )

    # Verify credentials and account status.
    credentials_valid = (
        user is not None
        and verify_password(
            data.password,
            user.password_hash,
        )
    )

    account_active = (
        user is not None
        and user.is_active
        and not user.is_banned
    )

    if not credentials_valid or not account_active:
        repository.record_login_attempt(
            session,
            email,
            ip_address,
            successful=False,
        )

        raise ValueError("Incorrect email or password.")

    # Upgrade legacy passwords after successful verification.
    if needs_password_upgrade(user.password_hash):
        user.password_hash = hash_password(data.password)
        user.updated_at = datetime.now(timezone.utc)

        session.add(user)
        session.commit()
        session.refresh(user)

    # Record successful login.
    repository.record_login_attempt(
        session,
        email,
        ip_address,
        successful=True,
    )

    refresh_token = _create_refresh_session(session, user)

    return {
        "response": _build_token_response(user),
        "refresh_token": refresh_token,
    }


def update_user_profile(
    session: Session,
    current_user: User,
    data: schemas.ProfileUpdateRequest,
) -> User:
    if data.name is not None:
        current_user.name = data.name

    if data.email is not None:
        new_email = normalize_email(str(data.email))

        if new_email != current_user.email:
            if data.current_password is None or not verify_password(
                data.current_password,
                current_user.password_hash,
            ):
                raise ValueError("Current password is incorrect.")

            existing_user = repository.get_user_by_email_excluding_id(
                session,
                new_email,
                current_user.id,
            )

            if existing_user is not None:
                raise ValueError(
                    "An account with this email already exists."
                )

            current_user.email = new_email

    current_user.updated_at = datetime.now(timezone.utc)

    try:
        session.add(current_user)
        session.commit()
        session.refresh(current_user)

    except IntegrityError:
        session.rollback()
        raise ValueError(
            "An account with this email already exists."
        )

    return current_user


def change_user_password(
    session: Session,
    current_user: User,
    data: schemas.PasswordChangeRequest,
) -> None:
    if not verify_password(
        data.current_password,
        current_user.password_hash,
    ):
        raise ValueError("Current password is incorrect.")

    current_user.password_hash = hash_password(data.new_password)
    current_user.updated_at = datetime.now(timezone.utc)

    try:
        session.add(current_user)
        repository.increment_user_token_version(
            session,
            current_user.id,
        )
        repository.revoke_user_refresh_sessions(
            session,
            current_user.id,
        )
        session.commit()

    except SQLAlchemyError:
        session.rollback()
        raise


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

    try:
        user = repository.lock_user(
            session,
            stored_session.user_id,
        )

        if user is None:
            raise ValueError("User account not found.")

        session.refresh(stored_session)
        session.refresh(user)

        # Reusing a revoked token invalidates the entire login session.
        if stored_session.revoked_at is not None:
            repository.revoke_refresh_family(
                session,
                stored_session.family_id,
                commit=False,
            )
            session.commit()
            raise ValueError("Refresh token has been revoked.")

        now = datetime.now(timezone.utc)

        expires_at = stored_session.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)

        if expires_at <= now:
            repository.revoke_refresh_family(
                session,
                stored_session.family_id,
                commit=False,
            )
            session.commit()
            raise ValueError("Refresh token has expired.")

        if not user.is_active or user.is_banned:
            repository.revoke_refresh_family(
                session,
                stored_session.family_id,
                commit=False,
            )
            session.commit()
            raise ValueError("This account is inactive or banned.")

        family_id = stored_session.family_id

        # Compare-and-set makes each refresh token usable only once.
        if not repository.revoke_refresh_session(
            session,
            stored_session,
            commit=False,
        ):
            repository.revoke_refresh_family(
                session,
                family_id,
                commit=False,
            )
            session.commit()
            raise ValueError("Refresh token has been revoked.")

        new_refresh_token = _create_refresh_session(
            session,
            user,
            family_id,
            commit=False,
        )
        session.commit()

    except SQLAlchemyError:
        session.rollback()
        raise

    return {
        "response": _build_token_response(user),
        "refresh_token": new_refresh_token,
    }


def logout(
    session: Session,
    raw_token: str | None,
    authenticated_user: User | None = None,
) -> User | None:
    stored_session = None
    if raw_token:
        stored_session = repository.get_refresh_session_by_hash(
            session,
            hash_refresh_token(raw_token),
        )

    cookie_user = None
    if stored_session is not None:
        cookie_user = repository.get_user_by_id(
            session,
            stored_session.user_id,
        )

    user = authenticated_user or cookie_user
    if user is None:
        return None

    try:
        user = repository.lock_user(
            session,
            user.id,
        )
        if user is None:
            session.rollback()
            return None

        if stored_session is not None:
            session.refresh(stored_session)
            cookie_user = repository.get_user_by_id(
                session,
                stored_session.user_id,
            )

        family_id = None
        if (
            stored_session is not None
            and cookie_user is not None
            and cookie_user.id == user.id
        ):
            family_id = stored_session.family_id

        family_revoked_before_logout = False
        if (
            authenticated_user is None
            and stored_session is not None
            and stored_session.revoked_at is not None
            and family_id is not None
        ):
            family_revoked_before_logout = (
                repository.revoke_refresh_family(
                    session,
                    family_id,
                    commit=False,
                )
            )

            if not family_revoked_before_logout:
                session.rollback()
                return user

        repository.increment_user_token_version(
            session,
            user.id,
        )

        if family_id is not None:
            if not family_revoked_before_logout:
                repository.revoke_refresh_family(
                    session,
                    family_id,
                    commit=False,
                )
        else:
            repository.revoke_user_refresh_sessions(
                session,
                user.id,
            )

        session.commit()

    except SQLAlchemyError:
        session.rollback()
        raise

    return user


def get_user_sessions(
    session: Session,
    user_id: UUID,
) -> list[dict]:
    refresh_sessions = repository.get_user_sessions(
        session,
        user_id,
    )

    # Group rotated refresh-token records by login session.
    families: dict[UUID, list[RefreshSession]] = {}

    for item in refresh_sessions:
        families.setdefault(item.family_id, []).append(item)

    result = []

    for family_id, family_tokens in families.items():
        created_at = min(
            item.created_at for item in family_tokens
        )

        expires_at = max(
            item.expires_at for item in family_tokens
        )

        revoked = all(
            item.revoked_at is not None
            for item in family_tokens
        )

        result.append(
            {
                "id": str(family_id),
                "created_at": created_at,
                "expires_at": expires_at,
                "revoked": revoked,
            }
        )

    result.sort(
        key=lambda item: item["created_at"],
        reverse=True,
    )

    return result


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
