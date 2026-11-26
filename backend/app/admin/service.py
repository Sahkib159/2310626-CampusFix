
import logging
import math

from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException, Request, status
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlmodel import Session

from app.auth.repository import (
    revoke_user_session_family as revoke_refresh_session_family,
    user_session_family_exists,
)
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
    get_admin_groups,
    get_admin_group_by_id,
    get_admin_group_request_count,
    delete_admin_group as delete_admin_group_record,
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
    BulkUserStatusResult,
    BulkUserOperationResponse,
    AdminGroupListResponse,
    AdminGroupResponse,
    AdminGroupDeleteResult,
    BulkGroupDeleteResponse,
)

from app.models.group import Group
from app.models.user import User
from app.models.refresh_session import RefreshSession
from app.audit.service import record_event


logger = logging.getLogger(__name__)

VALID_ROLES = {"STUDENT", "STAFF", "ADMIN"}


def list_groups(
    session: Session,
    page: int,
    page_size: int,
) -> AdminGroupListResponse:
    rows, total = get_admin_groups(
        session,
        offset=(page - 1) * page_size,
        limit=page_size,
    )

    return AdminGroupListResponse(
        groups=[
            AdminGroupResponse(
                id=group.id,
                name=group.name,
                description=group.description,
                owner_id=owner.id,
                owner_name=owner.name,
                owner_email=owner.email,
                member_count=member_count,
                request_count=request_count,
                is_archived=group.is_archived,
                created_at=group.created_at,
                updated_at=group.updated_at,
            )
            for group, owner, member_count, request_count in rows
        ],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=math.ceil(total / page_size) if total else 0,
    )


def _delete_loaded_group(
    session: Session,
    group: Group,
    current_admin: User,
    request: Request,
) -> AdminGroupDeleteResult:
    group_id = group.id
    group_name = group.name

    try:
        request_count = get_admin_group_request_count(session, group_id)
    except SQLAlchemyError:
        session.rollback()
        logger.exception(
            "Database error while checking requests for group %s",
            group_id,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="The group could not be deleted.",
        )

    if request_count > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot delete a group containing service requests.",
        )

    try:
        delete_admin_group_record(session, group)
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The group has related records and cannot be deleted.",
        )
    except SQLAlchemyError:
        session.rollback()
        logger.exception(
            "Database error while deleting group %s",
            group_id,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="The group could not be deleted.",
        )

    try:
        record_event(
            session,
            "GROUP_DELETED",
            request,
            actor_id=current_admin.id,
            details={
                "group_id": str(group_id),
                "group_name": group_name,
            },
        )
    except SQLAlchemyError:
        session.rollback()
        logger.exception(
            "Audit logging failed while deleting group %s",
            group_id,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="The group could not be deleted.",
        )

    return AdminGroupDeleteResult(
        group_id=group_id,
        group_name=group_name,
        success=True,
        message="Group deleted successfully.",
    )


def delete_group(
    session: Session,
    group_id: UUID,
    current_admin: User,
    request: Request,
) -> AdminGroupDeleteResult:
    group = get_admin_group_by_id(session, group_id)
    if group is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found.",
        )

    return _delete_loaded_group(
        session,
        group,
        current_admin,
        request,
    )


def bulk_delete_groups(
    session: Session,
    group_ids: list[UUID],
    current_admin: User,
    request: Request,
) -> BulkGroupDeleteResponse:
    results = []

    for group_id in group_ids:
        group = None
        try:
            group = get_admin_group_by_id(session, group_id)
            if group is None:
                results.append(
                    AdminGroupDeleteResult(
                        group_id=group_id,
                        success=False,
                        message="Group not found.",
                    )
                )
                continue

            results.append(
                _delete_loaded_group(
                    session,
                    group,
                    current_admin,
                    request,
                )
            )
        except HTTPException as exc:
            session.rollback()
            results.append(
                AdminGroupDeleteResult(
                    group_id=group_id,
                    group_name=group.name if group is not None else None,
                    success=False,
                    message=str(exc.detail),
                )
            )
        except Exception:
            session.rollback()
            logger.exception(
                "Unexpected error while bulk-deleting group %s",
                group_id,
            )
            results.append(
                AdminGroupDeleteResult(
                    group_id=group_id,
                    group_name=group.name if group is not None else None,
                    success=False,
                    message=(
                        "An unexpected error occurred while deleting "
                        "this group."
                    ),
                )
            )

    succeeded = sum(1 for item in results if item.success)
    return BulkGroupDeleteResponse(
        total=len(results),
        succeeded=succeeded,
        failed=len(results) - succeeded,
        results=results,
    )


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

    requests = get_user_service_requests(
        session,
        user_id,
    )

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

    refresh_sessions = get_user_refresh_sessions(
        session,
        user_id,
    )

    now = datetime.now(timezone.utc)

    families: dict[UUID, list[RefreshSession]] = {}

    for refresh_session in refresh_sessions:
        families.setdefault(
            refresh_session.family_id,
            [],
        ).append(refresh_session)

    sessions = []

    for family_id, family_tokens in families.items():
        created_at = min(
            item.created_at for item in family_tokens
        )
        expires_at = max(
            item.expires_at for item in family_tokens
        )
        revoked_dates = [
            item.revoked_at
            for item in family_tokens
            if item.revoked_at is not None
        ]
        revoked_at = (
            max(revoked_dates)
            if len(revoked_dates) == len(family_tokens)
            else None
        )
        is_active = any(
            item.revoked_at is None
            and item.expires_at
            > (
                now.replace(tzinfo=None)
                if item.expires_at.tzinfo is None
                else now
            )
            for item in family_tokens
        )

        sessions.append(
            AdminSessionResponse(
                id=family_id,
                created_at=created_at,
                expires_at=expires_at,
                revoked_at=revoked_at,
                is_active=is_active,
            )
        )

    sessions.sort(
        key=lambda item: item.created_at,
        reverse=True,
    )

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


def revoke_user_session_family(
    session: Session,
    user_id: UUID,
    family_id: UUID,
) -> tuple[User, bool]:
    target = get_admin_user_by_id(session, user_id)

    if target is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    if not user_session_family_exists(
        session,
        user_id,
        family_id,
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session family not found.",
        )

    revoked = revoke_refresh_session_family(
        session,
        user_id,
        family_id,
        commit=False,
    )

    return target, revoked


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


def bulk_ban_users(
    session: Session,
    current_admin: User,
    user_ids: list[UUID],
    reason: str,
    request: Request,
) -> BulkUserOperationResponse:

    results = []

    for user_id in user_ids:
        try:
            result = ban_user(
                session,
                current_admin,
                user_id,
                reason,
            )

            record_event(
                session,
                "USER_BANNED",
                request,
                actor_id=current_admin.id,
                target_user_id=result.id,
                email=result.email,
                details={"reason": reason.strip()},
            )

            results.append(
                BulkUserStatusResult(
                    user_id=user_id,
                    success=True,
                    message="User banned successfully.",
                    user=result,
                )
            )

        except HTTPException as exc:
            session.rollback()

            results.append(
                BulkUserStatusResult(
                    user_id=user_id,
                    success=False,
                    message=str(exc.detail),
                )
            )

        except Exception:
            session.rollback()

            logger.exception(
                "Unexpected error while bulk-banning user %s",
                user_id,
            )

            results.append(
                BulkUserStatusResult(
                    user_id=user_id,
                    success=False,
                    message=(
                        "An unexpected error occurred "
                        "while banning this user."
                    ),
                )
            )

    succeeded = sum(
        1 for item in results if item.success
    )

    return BulkUserOperationResponse(
        total=len(user_ids),
        succeeded=succeeded,
        failed=len(results) - succeeded,
        results=results,
    )


def bulk_unban_users(
    session: Session,
    current_admin: User,
    user_ids: list[UUID],
    request: Request,
) -> BulkUserOperationResponse:

    results = []

    for user_id in user_ids:
        try:
            result = unban_user(
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

            results.append(
                BulkUserStatusResult(
                    user_id=user_id,
                    success=True,
                    message="User unbanned successfully.",
                    user=result,
                )
            )

        except HTTPException as exc:
            session.rollback()

            results.append(
                BulkUserStatusResult(
                    user_id=user_id,
                    success=False,
                    message=str(exc.detail),
                )
            )

        except Exception:
            session.rollback()

            logger.exception(
                "Unexpected error while bulk-unbanning user %s",
                user_id,
            )

            results.append(
                BulkUserStatusResult(
                    user_id=user_id,
                    success=False,
                    message=(
                        "An unexpected error occurred "
                        "while unbanning this user."
                    ),
                )
            )

    succeeded = sum(
        1 for item in results if item.success
    )

    return BulkUserOperationResponse(
        total=len(user_ids),
        succeeded=succeeded,
        failed=len(results) - succeeded,
        results=results,
    )
