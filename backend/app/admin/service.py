
import math
from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException, status
from sqlmodel import Session

from app.admin.repository import (
    get_admin_users,
    get_admin_user_by_id,
    get_active_refresh_sessions,
    get_user_refresh_sessions,
    get_user_service_requests,
    get_user_groups,
    get_user_recent_activity,
    get_admin_dashboard_stats,
    get_recent_registrations,
)

from app.admin.schemas import (
    AdminUserListResponse,
    AdminUserResponse,
    AdminDashboardStatsResponse,
    RecentRegistrationResponse,
    AdminUserDetailResponse,
    AdminServiceRequestResponse,
    AdminGroupMembershipResponse,
    AdminSessionResponse,
)

from app.models.user import User


VALID_ROLES = {"STUDENT", "STAFF", "ADMIN"}


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


def get_user_detail(
    session: Session,
    user_id: UUID,
) -> AdminUserDetailResponse:

    user = get_admin_user_by_id(session, user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    # Service requests created by this user
    requests = get_user_service_requests(
        session,
        user_id,
    )

    # Groups owned or joined by this user
    group_records = get_user_groups(
        session,
        user_id,
    )

    groups = []
    seen_group_ids = set()

    for group, membership in group_records:
        if group.id in seen_group_ids:
            continue

        seen_group_ids.add(group.id)

        is_owner = group.owner_id == user_id

        groups.append(
            AdminGroupMembershipResponse(
                id=group.id,
                name=group.name,
                description=group.description,
                is_archived=group.is_archived,
                is_owner=is_owner,
                can_create_requests=(
                    True if is_owner
                    else membership.can_create_requests
                ),
                can_edit_requests=(
                    True if is_owner
                    else membership.can_edit_requests
                ),
                can_assign_requests=(
                    True if is_owner
                    else membership.can_assign_requests
                ),
                created_at=group.created_at,
            )
        )

    # All refresh sessions, without exposing token hashes
    refresh_sessions = get_user_refresh_sessions(
        session,
        user_id,
    )

    now = datetime.now(timezone.utc)

    sessions = []

    for refresh_session in refresh_sessions:
        expires_at = refresh_session.expires_at

        comparison_now = (
            now.replace(tzinfo=None)
            if expires_at.tzinfo is None
            else now
        )

        sessions.append(
            AdminSessionResponse(
                id=refresh_session.id,
                created_at=refresh_session.created_at,
                expires_at=expires_at,
                revoked_at=refresh_session.revoked_at,
                is_active=(
                    refresh_session.revoked_at is None
                    and expires_at > comparison_now
                ),
            )
        )

    # Recent audit activity involving this user
    activity = get_user_recent_activity(
        session,
        user_id,
        limit=10,
    )

    return AdminUserDetailResponse(
        user=AdminUserResponse.model_validate(user),
        service_requests=[
            AdminServiceRequestResponse.model_validate(request)
            for request in requests
        ],
        groups=groups,
        sessions=sessions,
        recent_activity=activity,
    )


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
    session.flush()
    session.refresh(target)

    return AdminUserResponse.model_validate(target)


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
    session.flush()
    session.refresh(target)

    return AdminUserResponse.model_validate(target)


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
    session.flush()
    session.refresh(target)

    return AdminUserResponse.model_validate(target)


def get_dashboard_stats(
    session: Session,
) -> AdminDashboardStatsResponse:

    stats = get_admin_dashboard_stats(session)

    return AdminDashboardStatsResponse(**stats)


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
