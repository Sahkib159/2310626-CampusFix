
import math
from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException, status
from sqlmodel import Session

from app.admin.repository import (
    get_admin_users,
    get_admin_user_by_id,
    get_active_refresh_sessions,
    get_admin_dashboard_stats,
    get_recent_registrations,
)

from app.admin.schemas import (
    AdminUserListResponse,
    AdminUserResponse,
    AdminDashboardStatsResponse,
    RecentRegistrationResponse,
)

from app.models.user import User


VALID_ROLES = {"STUDENT", "STAFF", "ADMIN"}


# --------------------------------------------------
# 1. List and search users
# --------------------------------------------------

def list_users(
    session: Session,
    search: str | None,
    role: str | None,
    is_active: bool | None,
    page: int,
    page_size: int,
) -> AdminUserListResponse:

    if role is not None:
        role = role.strip().upper()

        if role not in VALID_ROLES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid user role.",
            )

    offset = (page - 1) * page_size

    users, total = get_admin_users(
        session=session,
        search=search,
        role=role,
        is_active=is_active,
        offset=offset,
        limit=page_size,
    )

    return AdminUserListResponse(
        users=[
            AdminUserResponse.model_validate(user)
            for user in users
        ],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=math.ceil(total / page_size) if total else 0,
    )


# --------------------------------------------------
# 2. Ban a user
# --------------------------------------------------

def ban_user(
    session: Session,
    current_admin: User,
    user_id: UUID,
    reason: str,
) -> AdminUserResponse:

    target = get_admin_user_by_id(session, user_id)

    if target is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    if target.id == current_admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot ban your own account.",
        )

    if target.role == "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrators cannot be banned through this endpoint.",
        )

    if target.is_banned:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This user is already banned.",
        )

    clean_reason = reason.strip()

    if len(clean_reason) < 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ban reason must contain at least 3 characters.",
        )

    now = datetime.now(timezone.utc)

    target.is_banned = True
    target.ban_reason = clean_reason
    target.banned_at = now
    target.banned_by = current_admin.id

    active_sessions = get_active_refresh_sessions(
        session,
        target.id,
    )

    for refresh_session in active_sessions:
        refresh_session.revoked_at = now
        session.add(refresh_session)

    session.add(target)
    session.commit()
    session.refresh(target)

    return AdminUserResponse.model_validate(target)


# --------------------------------------------------
# 3. Unban a user
# --------------------------------------------------

def unban_user(
    session: Session,
    user_id: UUID,
) -> AdminUserResponse:

    target = get_admin_user_by_id(session, user_id)

    if target is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    if not target.is_banned:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This user is not currently banned.",
        )

    target.is_banned = False
    target.ban_reason = None
    target.banned_at = None
    target.banned_by = None

    session.add(target)
    session.commit()
    session.refresh(target)

    return AdminUserResponse.model_validate(target)


# --------------------------------------------------
# 4. Change user role
# --------------------------------------------------

def change_user_role(
    session: Session,
    current_admin: User,
    user_id: UUID,
    new_role: str,
) -> AdminUserResponse:

    target = get_admin_user_by_id(session, user_id)

    if target is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    if target.id == current_admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot change your own role.",
        )

    clean_role = new_role.strip().upper()

    if clean_role not in VALID_ROLES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user role.",
        )

    if target.role == clean_role:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already has this role.",
        )

    target.role = clean_role

    now = datetime.now(timezone.utc)

    active_sessions = get_active_refresh_sessions(
        session,
        target.id,
    )

    for refresh_session in active_sessions:
        refresh_session.revoked_at = now
        session.add(refresh_session)

    session.add(target)
    session.commit()
    session.refresh(target)

    return AdminUserResponse.model_validate(target)


# --------------------------------------------------
# 5. Admin dashboard statistics
# --------------------------------------------------

def get_dashboard_stats(
    session: Session,
) -> AdminDashboardStatsResponse:

    stats = get_admin_dashboard_stats(session)

    return AdminDashboardStatsResponse(**stats)


# --------------------------------------------------
# 6. Recent registrations
# --------------------------------------------------

def get_recent_users(
    session: Session,
    limit: int = 5,
) -> list[RecentRegistrationResponse]:

    users = get_recent_registrations(
        session=session,
        limit=limit,
    )

    return [
        RecentRegistrationResponse.model_validate(user)
        for user in users
    ]
