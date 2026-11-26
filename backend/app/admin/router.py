
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlmodel import Session

from database import get_session
from app.models.user import User
from app.auth.dependencies import get_current_admin
from app.admin import service

from app.admin.schemas import (
    AdminUserListResponse,
    AdminUserResponse,
    AdminUserDetailResponse,
    BanUserRequest,
    BulkBanUserRequest,
    BulkUnbanUserRequest,
    BulkUserOperationResponse,
    ChangeUserRoleRequest,
    AdminDashboardStatsResponse,
    RecentRegistrationResponse,
    AdminGroupListResponse,
    AdminGroupDeleteResult,
    BulkGroupDeleteRequest,
    BulkGroupDeleteResponse,
)

from app.audit.service import record_event
from app.audit.service import get_security_dashboard
from app.audit.schemas import SecurityDashboardResponse


router = APIRouter(
    prefix="/api/admin",
    tags=["Administration"],
)


@router.get(
    "/groups",
    response_model=AdminGroupListResponse,
)
def list_groups(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_admin: User = Depends(get_current_admin),
    session: Session = Depends(get_session),
):
    return service.list_groups(
        session,
        page,
        page_size,
    )


@router.post(
    "/groups/bulk-delete",
    response_model=BulkGroupDeleteResponse,
)
def bulk_delete_groups(
    data: BulkGroupDeleteRequest,
    request: Request,
    current_admin: User = Depends(get_current_admin),
    session: Session = Depends(get_session),
):
    return service.bulk_delete_groups(
        session,
        data.group_ids,
        current_admin,
        request,
    )


@router.delete(
    "/groups/{group_id}",
    response_model=AdminGroupDeleteResult,
)
def delete_group(
    group_id: UUID,
    request: Request,
    current_admin: User = Depends(get_current_admin),
    session: Session = Depends(get_session),
):
    return service.delete_group(
        session,
        group_id,
        current_admin,
        request,
    )


@router.get(
    "/users",
    response_model=AdminUserListResponse,
)
def list_users(
    search: str | None = Query(default=None, max_length=255),
    role: str | None = Query(default=None),
    is_active: bool | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_admin: User = Depends(get_current_admin),
    session: Session = Depends(get_session),
):
    return service.list_users(
        session,
        search,
        role,
        is_active,
        page,
        page_size,
    )


# Keep bulk routes before individual user routes.
@router.post(
    "/users/bulk-ban",
    response_model=BulkUserOperationResponse,
)
def bulk_ban_users(
    data: BulkBanUserRequest,
    request: Request,
    current_admin: User = Depends(get_current_admin),
    session: Session = Depends(get_session),
):
    return service.bulk_ban_users(
        session=session,
        current_admin=current_admin,
        user_ids=data.user_ids,
        reason=data.reason,
        request=request,
    )


@router.post(
    "/users/bulk-unban",
    response_model=BulkUserOperationResponse,
)
def bulk_unban_users(
    data: BulkUnbanUserRequest,
    request: Request,
    current_admin: User = Depends(get_current_admin),
    session: Session = Depends(get_session),
):
    return service.bulk_unban_users(
        session=session,
        current_admin=current_admin,
        user_ids=data.user_ids,
        request=request,
    )


@router.get(
    "/users/{user_id}",
    response_model=AdminUserDetailResponse,
)
def get_user_detail(
    user_id: UUID,
    current_admin: User = Depends(get_current_admin),
    session: Session = Depends(get_session),
):
    return service.get_user_detail(
        session,
        user_id,
    )


@router.delete("/users/{user_id}/sessions/{family_id}")
def revoke_user_session_family(
    user_id: UUID,
    family_id: UUID,
    request: Request,
    current_admin: User = Depends(get_current_admin),
    session: Session = Depends(get_session),
):
    target, revoked = service.revoke_user_session_family(
        session,
        user_id,
        family_id,
    )

    record_event(
        session,
        "USER_SESSION_REVOKED",
        request,
        actor_id=current_admin.id,
        target_user_id=target.id,
        email=target.email,
        details={
            "family_id": str(family_id),
            "changed": revoked,
        },
    )

    return {"message": "Session family revoked successfully."}


@router.post(
    "/users/{user_id}/ban",
    response_model=AdminUserResponse,
)
def ban_user(
    user_id: UUID,
    data: BanUserRequest,
    request: Request,
    current_admin: User = Depends(get_current_admin),
    session: Session = Depends(get_session),
):
    result = service.ban_user(
        session,
        current_admin,
        user_id,
        data.reason,
    )

    record_event(
        session,
        "USER_BANNED",
        request,
        actor_id=current_admin.id,
        target_user_id=result.id,
        email=result.email,
        details={"reason": data.reason.strip()},
    )

    return result


@router.post(
    "/users/{user_id}/unban",
    response_model=AdminUserResponse,
)
def unban_user(
    user_id: UUID,
    request: Request,
    current_admin: User = Depends(get_current_admin),
    session: Session = Depends(get_session),
):
    result = service.unban_user(
        session,
        user_id,
    )

    record_event(
        session,
        "USER_UNBANNED",
        request,
        actor_id=current_admin.id,
        target_user_id=result.id,
        email=result.email,
    )

    return result


@router.patch(
    "/users/{user_id}/role",
    response_model=AdminUserResponse,
)
def change_user_role(
    user_id: UUID,
    data: ChangeUserRoleRequest,
    request: Request,
    current_admin: User = Depends(get_current_admin),
    session: Session = Depends(get_session),
):
    target_before = service.get_admin_user_by_id(
        session,
        user_id,
    )

    old_role = (
        target_before.role
        if target_before
        else None
    )

    result = service.change_user_role(
        session,
        current_admin,
        user_id,
        data.role,
    )

    record_event(
        session,
        "USER_ROLE_CHANGED",
        request,
        actor_id=current_admin.id,
        target_user_id=result.id,
        email=result.email,
        details={
            "old_role": old_role,
            "new_role": result.role,
        },
    )

    return result


@router.get(
    "/dashboard/stats",
    response_model=AdminDashboardStatsResponse,
)
def dashboard_stats(
    current_admin: User = Depends(get_current_admin),
    session: Session = Depends(get_session),
):
    return service.get_dashboard_stats(session)


@router.get(
    "/dashboard/recent-users",
    response_model=list[RecentRegistrationResponse],
)
def recent_users(
    limit: int = Query(default=5, ge=1, le=20),
    current_admin: User = Depends(get_current_admin),
    session: Session = Depends(get_session),
):
    return service.get_recent_users(
        session,
        limit,
    )


@router.get(
    "/security/failed-logins",
    response_model=SecurityDashboardResponse,
)
def security_failed_logins(
    start_date: datetime | None = Query(default=None),
    end_date: datetime | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    current_admin: User = Depends(get_current_admin),
    session: Session = Depends(get_session),
):
    """Return login security events and summaries for at most 90 days."""
    return get_security_dashboard(
        session,
        start_date=start_date,
        end_date=end_date,
        page=page,
        page_size=page_size,
    )
