
from uuid import UUID

from sqlmodel import Session, select, col, func

from app.models.user import User
from app.models.refresh_session import RefreshSession


def get_admin_users(
    session: Session,
    search: str | None,
    role: str | None,
    is_active: bool | None,
    offset: int,
    limit: int,
) -> tuple[list[User], int]:

    statement = select(User)

    if search:
        search_term = f"%{search.strip()}%"
        statement = statement.where(
            col(User.name).ilike(search_term)
            | col(User.email).ilike(search_term)
        )

    if role:
        statement = statement.where(User.role == role)

    if is_active is not None:
        statement = statement.where(User.is_active == is_active)

    count_statement = (
        select(func.count())
        .select_from(statement.subquery())
    )
    total = session.exec(count_statement).one()

    users_statement = (
        statement
        .order_by(User.created_at.desc())
        .offset(offset)
        .limit(limit)
    )

    users = list(session.exec(users_statement).all())

    return users, total


def get_admin_user_by_id(
    session: Session,
    user_id: UUID,
) -> User | None:
    return session.get(User, user_id)


def get_active_refresh_sessions(
    session: Session,
    user_id: UUID,
) -> list[RefreshSession]:
    statement = select(RefreshSession).where(
        RefreshSession.user_id == user_id,
        RefreshSession.revoked_at.is_(None),
    )

    return list(session.exec(statement).all())


# Admin dashboard statistics
def get_admin_dashboard_stats(
    session: Session,
) -> dict[str, int]:

    def count_users(*conditions) -> int:
        statement = select(func.count()).select_from(User)

        if conditions:
            statement = statement.where(*conditions)

        return session.exec(statement).one()

    return {
        "total_users": count_users(),
        "total_students": count_users(User.role == "STUDENT"),
        "total_staff": count_users(User.role == "STAFF"),
        "total_admins": count_users(User.role == "ADMIN"),
        "active_users": count_users(User.is_active == True),
        "inactive_users": count_users(User.is_active == False),
        "banned_users": count_users(User.is_banned == True),
    }


# Recently registered users
def get_recent_registrations(
    session: Session,
    limit: int = 5,
) -> list[User]:

    statement = (
        select(User)
        .order_by(User.created_at.desc())
        .limit(limit)
    )

    return list(session.exec(statement).all())
