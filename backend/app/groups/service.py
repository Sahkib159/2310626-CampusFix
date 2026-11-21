
from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException, status
from sqlmodel import Session, select

from app.models.group import Group, GroupMember
from app.models.service_request import ServiceRequest
from app.models.user import User
from app.groups import repository, schemas


def get_membership_context(
    session: Session,
    group: Group,
    current_user: User,
) -> tuple[bool, GroupMember | None]:
    """
    Determine if current_user is the owner or a member of the group.
    """
    is_owner = group.owner_id == current_user.id
    member = None

    if not is_owner:
        member = repository.get_group_member(
            session,
            group.id,
            current_user.id,
        )

    return is_owner, member


def require_group_access(
    session: Session,
    group_id: UUID,
    current_user: User,
) -> tuple[Group, bool, GroupMember | None]:
    """
    Allow access only to the group owner or an actual group member.
    Return 404 for everyone else to prevent group enumeration.
    """
    group = repository.get_group_by_id(session, group_id)

    if group is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found.",
        )

    is_owner, member = get_membership_context(
        session,
        group,
        current_user,
    )

    if not is_owner and member is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found.",
        )

    return group, is_owner, member


def require_group_owner(
    session: Session,
    group_id: UUID,
    current_user: User,
) -> Group:
    """
    Ensure the current user is strictly the group owner.
    """
    group = repository.get_group_by_id(session, group_id)

    if group is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found.",
        )

    if group.owner_id != current_user.id:
        _, member = get_membership_context(
            session,
            group,
            current_user,
        )

        if member is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Group not found.",
            )

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the group owner can perform this action.",
        )

    return group


def require_active_group(group: Group) -> None:
    """
    Ensure the group is active (not archived) for mutation operations.
    """
    if group.is_archived:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Group is archived. All modifications are blocked.",
        )


def require_group_permission(
    session: Session,
    group_id: UUID,
    current_user: User,
    permission_attr: str,
) -> tuple[Group, bool]:
    """
    Verify that current_user has the requested permission in the group.
    Group owner always holds all permissions.
    """
    group, is_owner, member = require_group_access(
        session,
        group_id,
        current_user,
    )

    if is_owner:
        return group, True

    if member is not None and getattr(member, permission_attr, False) is True:
        return group, False

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You do not have permission to perform this action in this group.",
    )


def create_group(
    session: Session,
    data: schemas.GroupCreate,
    current_user: User,
) -> schemas.GroupResponse:
    group = Group(
        name=data.name,
        description=data.description,
        owner_id=current_user.id,
        is_archived=False,
    )

    saved = repository.create_group(session, group)

    return schemas.GroupResponse(
        id=saved.id,
        name=saved.name,
        description=saved.description,
        owner_id=saved.owner_id,
        is_archived=saved.is_archived,
        created_at=saved.created_at,
        updated_at=saved.updated_at,
        is_owner=True,
        permissions=schemas.GroupPermissions(
            can_create_requests=True,
            can_edit_requests=True,
            can_assign_requests=True,
        ),
    )


def get_user_groups(
    session: Session,
    current_user: User,
    include_archived: bool = True,
) -> list[schemas.GroupResponse]:
    groups = repository.get_user_groups(
        session,
        current_user.id,
        include_archived=include_archived,
    )

    results = []

    for group in groups:
        is_owner = group.owner_id == current_user.id

        if is_owner:
            perms = schemas.GroupPermissions(
                can_create_requests=True,
                can_edit_requests=True,
                can_assign_requests=True,
            )
        else:
            member = repository.get_group_member(
                session,
                group.id,
                current_user.id,
            )

            perms = schemas.GroupPermissions(
                can_create_requests=member.can_create_requests if member else False,
                can_edit_requests=member.can_edit_requests if member else False,
                can_assign_requests=member.can_assign_requests if member else False,
            )

        results.append(
            schemas.GroupResponse(
                id=group.id,
                name=group.name,
                description=group.description,
                owner_id=group.owner_id,
                is_archived=group.is_archived,
                created_at=group.created_at,
                updated_at=group.updated_at,
                is_owner=is_owner,
                permissions=perms,
            )
        )

    return results


def get_group_details(
    session: Session,
    group_id: UUID,
    current_user: User,
) -> schemas.GroupResponse:
    group, is_owner, member = require_group_access(
        session,
        group_id,
        current_user,
    )

    if is_owner:
        perms = schemas.GroupPermissions(
            can_create_requests=True,
            can_edit_requests=True,
            can_assign_requests=True,
        )
    else:
        perms = schemas.GroupPermissions(
            can_create_requests=member.can_create_requests,
            can_edit_requests=member.can_edit_requests,
            can_assign_requests=member.can_assign_requests,
        )

    return schemas.GroupResponse(
        id=group.id,
        name=group.name,
        description=group.description,
        owner_id=group.owner_id,
        is_archived=group.is_archived,
        created_at=group.created_at,
        updated_at=group.updated_at,
        is_owner=is_owner,
        permissions=perms,
    )


def update_group(
    session: Session,
    group_id: UUID,
    data: schemas.GroupUpdate,
    current_user: User,
) -> schemas.GroupResponse:
    group = require_group_owner(session, group_id, current_user)
    require_active_group(group)

    if data.name is not None:
        group.name = data.name

    if data.description is not None:
        group.description = data.description

    group.updated_at = datetime.now(timezone.utc)
    updated = repository.update_group(session, group)

    return schemas.GroupResponse(
        id=updated.id,
        name=updated.name,
        description=updated.description,
        owner_id=updated.owner_id,
        is_archived=updated.is_archived,
        created_at=updated.created_at,
        updated_at=updated.updated_at,
        is_owner=True,
        permissions=schemas.GroupPermissions(
            can_create_requests=True,
            can_edit_requests=True,
            can_assign_requests=True,
        ),
    )


def archive_group(
    session: Session,
    group_id: UUID,
    current_user: User,
) -> schemas.GroupResponse:
    group = require_group_owner(session, group_id, current_user)

    if not group.is_archived:
        group.is_archived = True
        group.updated_at = datetime.now(timezone.utc)
        group = repository.update_group(session, group)

    return schemas.GroupResponse(
        id=group.id,
        name=group.name,
        description=group.description,
        owner_id=group.owner_id,
        is_archived=group.is_archived,
        created_at=group.created_at,
        updated_at=group.updated_at,
        is_owner=True,
        permissions=schemas.GroupPermissions(
            can_create_requests=True,
            can_edit_requests=True,
            can_assign_requests=True,
        ),
    )


def unarchive_group(
    session: Session,
    group_id: UUID,
    current_user: User,
) -> schemas.GroupResponse:
    group = require_group_owner(session, group_id, current_user)

    if group.is_archived:
        group.is_archived = False
        group.updated_at = datetime.now(timezone.utc)
        group = repository.update_group(session, group)

    return schemas.GroupResponse(
        id=group.id,
        name=group.name,
        description=group.description,
        owner_id=group.owner_id,
        is_archived=group.is_archived,
        created_at=group.created_at,
        updated_at=group.updated_at,
        is_owner=True,
        permissions=schemas.GroupPermissions(
            can_create_requests=True,
            can_edit_requests=True,
            can_assign_requests=True,
        ),
    )


def delete_group(
    session: Session,
    group_id: UUID,
    current_user: User,
) -> dict[str, str]:
    group = require_group_owner(session, group_id, current_user)
    require_active_group(group)

    request_count = repository.get_group_requests_count(
        session,
        group.id,
    )

    if request_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete group containing service requests. Archive the group instead to preserve historical records.",
        )

    repository.delete_group(session, group)

    return {
        "message": "Group deleted successfully.",
        "id": str(group_id),
    }


def get_group_members(
    session: Session,
    group_id: UUID,
    current_user: User,
) -> list[schemas.GroupMemberResponse]:
    group, _, _ = require_group_access(
        session,
        group_id,
        current_user,
    )

    owner_user = session.get(User, group.owner_id)

    if owner_user is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Group owner record missing.",
        )

    owner_entry = schemas.GroupMemberResponse(
        id=group.id,
        group_id=group.id,
        user_id=owner_user.id,
        user_name=owner_user.name,
        user_email=owner_user.email,
        role="OWNER",
        is_owner=True,
        can_create_requests=True,
        can_edit_requests=True,
        can_assign_requests=True,
        created_at=group.created_at,
    )

    members_with_users = repository.get_group_members_with_users(
        session,
        group.id,
    )

    member_entries = [
        schemas.GroupMemberResponse(
            id=member.id,
            group_id=member.group_id,
            user_id=user.id,
            user_name=user.name,
            user_email=user.email,
            role="MEMBER",
            is_owner=False,
            can_create_requests=member.can_create_requests,
            can_edit_requests=member.can_edit_requests,
            can_assign_requests=member.can_assign_requests,
            created_at=member.created_at,
        )
        for member, user in members_with_users
    ]

    return [owner_entry, *member_entries]


def add_group_member(
    session: Session,
    group_id: UUID,
    data: schemas.MemberAddRequest,
    current_user: User,
) -> schemas.GroupMemberResponse:
    group = require_group_owner(session, group_id, current_user)
    require_active_group(group)

    target_user = session.exec(
        select(User).where(User.email == data.email.lower())
    ).first()

    if target_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User with this email not found.",
        )

    if target_user.id == group.owner_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already the group owner.",
        )

    existing = repository.get_group_member(
        session,
        group.id,
        target_user.id,
    )

    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already a member of this group.",
        )

    member = GroupMember(
        group_id=group.id,
        user_id=target_user.id,
        can_create_requests=data.can_create_requests,
        can_edit_requests=data.can_edit_requests,
        can_assign_requests=data.can_assign_requests,
    )

    saved = repository.add_group_member(session, member)

    return schemas.GroupMemberResponse(
        id=saved.id,
        group_id=saved.group_id,
        user_id=target_user.id,
        user_name=target_user.name,
        user_email=target_user.email,
        role="MEMBER",
        is_owner=False,
        can_create_requests=saved.can_create_requests,
        can_edit_requests=saved.can_edit_requests,
        can_assign_requests=saved.can_assign_requests,
        created_at=saved.created_at,
    )


def update_group_member_permissions(
    session: Session,
    group_id: UUID,
    member_user_id: UUID,
    data: schemas.MemberUpdateRequest,
    current_user: User,
) -> schemas.GroupMemberResponse:
    group = require_group_owner(session, group_id, current_user)
    require_active_group(group)

    if member_user_id == group.owner_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot modify permissions of the group owner.",
        )

    member = repository.get_group_member(
        session,
        group.id,
        member_user_id,
    )

    if member is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found in this group.",
        )

    if data.can_create_requests is not None:
        member.can_create_requests = data.can_create_requests

    if data.can_edit_requests is not None:
        member.can_edit_requests = data.can_edit_requests

    if data.can_assign_requests is not None:
        member.can_assign_requests = data.can_assign_requests

    member.updated_at = datetime.now(timezone.utc)
    updated = repository.update_group_member(session, member)

    target_user = session.get(User, member_user_id)

    return schemas.GroupMemberResponse(
        id=updated.id,
        group_id=updated.group_id,
        user_id=target_user.id,
        user_name=target_user.name,
        user_email=target_user.email,
        role="MEMBER",
        is_owner=False,
        can_create_requests=updated.can_create_requests,
        can_edit_requests=updated.can_edit_requests,
        can_assign_requests=updated.can_assign_requests,
        created_at=updated.created_at,
    )


def remove_group_member(
    session: Session,
    group_id: UUID,
    member_user_id: UUID,
    current_user: User,
) -> dict[str, str]:
    if member_user_id == current_user.id:
        group, is_owner, member = require_group_access(
            session,
            group_id,
            current_user,
        )
        require_active_group(group)

        if is_owner:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Group owner cannot leave the group. Delete or archive the group instead.",
            )
    else:
        group = require_group_owner(
            session,
            group_id,
            current_user,
        )
        require_active_group(group)

        if member_user_id == group.owner_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot remove the group owner.",
            )

        member = repository.get_group_member(
            session,
            group.id,
            member_user_id,
        )

        if member is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Member not found in this group.",
            )

    repository.delete_group_member(session, member)

    return {"message": "Member removed successfully."}


# GROUP SERVICE REQUESTS


def get_group_requests(
    session: Session,
    group_id: UUID,
    current_user: User,
) -> list[ServiceRequest]:
    require_group_access(session, group_id, current_user)

    return repository.get_group_requests(session, group_id)


def create_group_request(
    session: Session,
    group_id: UUID,
    data: schemas.GroupServiceRequestCreate,
    current_user: User,
) -> ServiceRequest:
    group, _ = require_group_permission(
        session,
        group_id,
        current_user,
        "can_create_requests",
    )
    require_active_group(group)

    new_request = ServiceRequest(
        user_id=current_user.id,
        group_id=group.id,
        title=data.title,
        description=data.description,
        category=data.category,
        status="pending",
    )

    return repository.create_group_request(session, new_request)


def get_group_request(
    session: Session,
    group_id: UUID,
    request_id: int,
    current_user: User,
) -> ServiceRequest:
    req = repository.get_group_request_by_id(
        session,
        group_id,
        request_id,
    )

    if req is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service request not found.",
        )

    if current_user.role == "STAFF" and req.assigned_to == current_user.id:
        return req

    require_group_access(session, group_id, current_user)

    return req


def update_group_request(
    session: Session,
    group_id: UUID,
    request_id: int,
    data: schemas.GroupServiceRequestUpdate,
    current_user: User,
) -> ServiceRequest:
    group, _ = require_group_permission(
        session,
        group_id,
        current_user,
        "can_edit_requests",
    )
    require_active_group(group)

    req = repository.get_group_request_by_id(
        session,
        group_id,
        request_id,
    )

    if req is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service request not found.",
        )

    if req.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only edit pending requests.",
        )

    req.title = data.title
    req.description = data.description
    req.category = data.category
    req.updated_at = datetime.now(timezone.utc)

    return repository.update_group_request(session, req)


def delete_group_request(
    session: Session,
    group_id: UUID,
    request_id: int,
    current_user: User,
) -> dict[str, str | int]:
    group = require_group_owner(
        session,
        group_id,
        current_user,
    )
    require_active_group(group)

    req = repository.get_group_request_by_id(
        session,
        group_id,
        request_id,
    )

    if req is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service request not found.",
        )

    if req.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete pending requests.",
        )

    repository.delete_group_request(session, req)

    return {
        "message": "Service request deleted successfully.",
        "id": request_id,
    }


def assign_group_request_staff(
    session: Session,
    group_id: UUID,
    request_id: int,
    data: schemas.GroupAssignStaffRequest,
    current_user: User,
) -> ServiceRequest:
    group, _ = require_group_permission(
        session,
        group_id,
        current_user,
        "can_assign_requests",
    )
    require_active_group(group)

    req = repository.get_group_request_by_id(
        session,
        group_id,
        request_id,
    )

    if req is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service request not found.",
        )

    if req.status in ["resolved", "cancelled"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot assign a completed or cancelled request.",
        )

    try:
        staff_id = UUID(data.staff_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid staff ID.",
        )

    staff_member = session.get(User, staff_id)

    if staff_member is None or staff_member.role != "STAFF":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Selected user is not a valid staff member.",
        )

    req.assigned_to = staff_member.id
    req.status = "assigned"
    req.updated_at = datetime.now(timezone.utc)

    return repository.update_group_request(session, req)


def unassign_group_request_staff(
    session: Session,
    group_id: UUID,
    request_id: int,
    current_user: User,
) -> ServiceRequest:
    group, _ = require_group_permission(
        session,
        group_id,
        current_user,
        "can_assign_requests",
    )
    require_active_group(group)

    req = repository.get_group_request_by_id(
        session,
        group_id,
        request_id,
    )

    if req is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service request not found.",
        )

    if req.status in ["resolved", "cancelled"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot unassign a completed or cancelled request.",
        )

    req.assigned_to = None
    req.status = "pending"
    req.updated_at = datetime.now(timezone.utc)

    return repository.update_group_request(session, req)
