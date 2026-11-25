
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import update
from sqlmodel import Session, select

from app.models.user import User
from app.models.refresh_session import RefreshSession
from app.models.login_attempt import LoginAttempt
from app.auth.normalization import normalize_email


# --------------------------------------------------
# USER OPERATIONS
# --------------------------------------------------

def get_user_by_email(
    session: Session,
    email: str,
) -> User | None:
    statement = select(User).where(User.email == email)
    return session.exec(statement).first()


def get_user_by_email_excluding_id(
    session: Session,
    email: str,
    user_id: UUID,
) -> User | None:
    statement = select(User).where(
        User.email == email,
        User.id != user_id,
    )
    return session.exec(statement).first()


def get_user_by_id(
    session: Session,
    user_id: UUID,
) -> User | None:
    return session.get(User, user_id)


def increment_user_token_version(
    session: Session,
    user_id: UUID,
) -> None:
    statement = (
        update(User)
        .where(User.id == user_id)
        .values(token_version=User.token_version + 1)
    )

    session.exec(statement)


def create_user(
    session: Session,
    user: User,
) -> User:
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


# --------------------------------------------------
# REFRESH SESSION OPERATIONS
# --------------------------------------------------

def create_refresh_session(
    session: Session,
    refresh_session: RefreshSession,
) -> RefreshSession:
    session.add(refresh_session)
    session.commit()
    session.refresh(refresh_session)
    return refresh_session


def get_refresh_session_by_hash(
    session: Session,
    token_hash: str,
) -> RefreshSession | None:
    statement = select(RefreshSession).where(
        RefreshSession.token_hash == token_hash
    )
    return session.exec(statement).first()


def revoke_refresh_session(
    session: Session,
    refresh_session: RefreshSession,
) -> None:
    refresh_session.revoked_at = datetime.now(timezone.utc)
    session.add(refresh_session)
    session.commit()


def revoke_refresh_family(
    session: Session,
    family_id: UUID,
    commit: bool = True,
) -> None:
    _revoke_refresh_family(
        session,
        family_id,
    )

    if commit:
        session.commit()


def _revoke_refresh_family(
    session: Session,
    family_id: UUID,
) -> None:
    statement = select(RefreshSession).where(
        RefreshSession.family_id == family_id,
        RefreshSession.revoked_at.is_(None),
    )

    refresh_sessions = session.exec(statement).all()
    now = datetime.now(timezone.utc)

    for refresh_session in refresh_sessions:
        refresh_session.revoked_at = now
        session.add(refresh_session)


def revoke_user_refresh_sessions(
    session: Session,
    user_id: UUID,
) -> None:
    statement = (
        update(RefreshSession)
        .where(
            RefreshSession.user_id == user_id,
            RefreshSession.revoked_at.is_(None),
        )
        .values(revoked_at=datetime.now(timezone.utc))
    )

    session.exec(statement)


def get_user_sessions(
    session: Session,
    user_id: UUID,
) -> list[RefreshSession]:
    statement = (
        select(RefreshSession)
        .where(RefreshSession.user_id == user_id)
        .order_by(RefreshSession.created_at.desc())
    )

    return list(session.exec(statement).all())


def revoke_user_session_family(
    session: Session,
    user_id: UUID,
    family_id: UUID,
    commit: bool = True,
) -> bool:
    statement = (
        update(RefreshSession)
        .where(
            RefreshSession.user_id == user_id,
            RefreshSession.family_id == family_id,
            RefreshSession.revoked_at.is_(None),
        )
        .values(revoked_at=datetime.now(timezone.utc))
    )

    result = session.exec(statement)

    if commit:
        session.commit()

    return result.rowcount > 0


def user_session_family_exists(
    session: Session,
    user_id: UUID,
    family_id: UUID,
) -> bool:
    statement = select(RefreshSession.id).where(
        RefreshSession.user_id == user_id,
        RefreshSession.family_id == family_id,
    )

    return session.exec(statement).first() is not None


def revoke_user_session(
    session: Session,
    user_id: UUID,
    session_id: UUID,
) -> bool:
    # session_id represents the login session's family_id.
    statement = select(RefreshSession).where(
        RefreshSession.family_id == session_id,
        RefreshSession.user_id == user_id,
    )

    refresh_session = session.exec(statement).first()

    if refresh_session is None:
        return False

    # Revoke every refresh token belonging to this login session.
    revoke_user_session_family(
        session,
        user_id,
        session_id,
    )

    return True


# --------------------------------------------------
# LOGIN ATTEMPT OPERATIONS
# --------------------------------------------------

def record_login_attempt(
    session: Session,
    email: str,
    ip_address: str,
    successful: bool,
) -> LoginAttempt:
    """Persist one successful or failed login attempt."""

    attempt = LoginAttempt(
        email=normalize_email(email),
        ip_address=ip_address,
        successful=successful,
        attempted_at=datetime.now(timezone.utc),
    )

    session.add(attempt)
    session.commit()
    session.refresh(attempt)

    return attempt


def count_failed_login_attempts_by_email(
    session: Session,
    email: str,
    since: datetime,
) -> int:
    """Count failed login attempts for an email since a given time."""

    statement = select(LoginAttempt).where(
        LoginAttempt.email == normalize_email(email),
        LoginAttempt.successful.is_(False),
        LoginAttempt.attempted_at >= since,
    )

    return len(session.exec(statement).all())


def count_failed_login_attempts_by_ip(
    session: Session,
    ip_address: str,
    since: datetime,
) -> int:
    """Count failed login attempts from an IP since a given time."""

    statement = select(LoginAttempt).where(
        LoginAttempt.ip_address == ip_address,
        LoginAttempt.successful.is_(False),
        LoginAttempt.attempted_at >= since,
    )

    return len(session.exec(statement).all())
