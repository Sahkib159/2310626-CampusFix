
from datetime import datetime, timezone
from uuid import UUID

from sqlmodel import Session, select

from app.models.user import User
from app.models.refresh_session import RefreshSession


def get_user_by_email(
    session: Session,
    email: str,
) -> User | None:
    statement = select(User).where(User.email == email)
    return session.exec(statement).first()


def get_user_by_id(
    session: Session,
    user_id: UUID,
) -> User | None:
    return session.get(User, user_id)


def create_user(
    session: Session,
    user: User,
) -> User:
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


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
) -> None:
    statement = select(RefreshSession).where(
        RefreshSession.family_id == family_id,
        RefreshSession.revoked_at.is_(None),
    )

    sessions = session.exec(statement).all()
    now = datetime.now(timezone.utc)

    for refresh_session in sessions:
        refresh_session.revoked_at = now
        session.add(refresh_session)

    session.commit()


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


def revoke_user_session(
    session: Session,
    user_id: UUID,
    session_id: UUID,
) -> bool:
    statement = select(RefreshSession).where(
        RefreshSession.id == session_id,
        RefreshSession.user_id == user_id,
    )

    refresh_session = session.exec(statement).first()

    if refresh_session is None:
        return False

    if refresh_session.revoked_at is None:
        refresh_session.revoked_at = datetime.now(timezone.utc)
        session.add(refresh_session)
        session.commit()

    return True
