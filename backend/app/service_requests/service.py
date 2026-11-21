
from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException
from sqlmodel import Session, select

from app import schemas
from app.models.service_request import ServiceRequest
from app.models.user import User
from app.models.group import Group, GroupMember
from app.auth.permissions import (
    STUDENT,
    STAFF,
    ADMIN,
    require_user_role,
)
from app.service_requests import repository


def create_request(
    session: Session,
    data: schemas.ServiceRequestCreate,
    current_user: User,
):
    require_user_role(current_user, STUDENT, ADMIN)

    new_request = ServiceRequest(
        user_id=current_user.id,
        title=data.title,
        description=data.description,
        category=data.category,
        status="pending",
    )
    return repository.create_request(session, new_request)


def get_all_requests(session: Session, current_user: User):
    return repository.get_all_requests(
        session,
        user_id=current_user.id,
        role=current_user.role,
    )


def get_request(session: Session, request_id: int, current_user: User):
    request = repository.get_request_by_id(
        session,
        request_id=request_id,
        user_id=current_user.id,
        role=current_user.role,
    )

    if request is None:
        raise HTTPException(
            status_code=404,
            detail="Service request not found.",
        )

    return request


def update_request(
    session: Session,
    request_id: int,
    data: schemas.ServiceRequestUpdate,
    current_user: User,
):
    request = get_request(session, request_id, current_user)

    if request.group_id is not None:
        group = session.get(Group, request.group_id)

        if group is None:
            raise HTTPException(
                status_code=404,
                detail="Service request not found.",
            )

        if group.is_archived:
            raise HTTPException(
                status_code=400,
                detail="Group is archived. All modifications are blocked.",
            )

        if current_user.role in (STUDENT, ADMIN):
            is_owner = group.owner_id == current_user.id

            member = None
            if not is_owner:
                member = session.exec(
                    select(GroupMember).where(
                        GroupMember.group_id == group.id,
                        GroupMember.user_id == current_user.id,
                    )
                ).first()

            if not is_owner and (
                member is None or not member.can_edit_requests
            ):
                raise HTTPException(
                    status_code=403,
                    detail="You do not have permission to edit requests in this group.",
                )

            if request.status != "pending":
                raise HTTPException(
                    status_code=403,
                    detail="You can only edit pending requests.",
                )

            request.title = data.title
            request.description = data.description
            request.category = data.category

        elif current_user.role == STAFF:
            request.status = data.status

        else:
            raise HTTPException(
                status_code=403,
                detail="You are not allowed to update this request.",
            )

    elif current_user.role == STUDENT:
        if request.status != "pending":
            raise HTTPException(
                status_code=403,
                detail="You can only edit pending requests.",
            )

        request.title = data.title
        request.description = data.description
        request.category = data.category

    elif current_user.role == STAFF:
        request.status = data.status

    elif current_user.role == ADMIN:
        request.title = data.title
        request.description = data.description
        request.category = data.category
        request.status = data.status

    else:
        raise HTTPException(
            status_code=403,
            detail="You are not allowed to update service requests.",
        )

    request.updated_at = datetime.now(timezone.utc)

    return repository.update_request(session, request)


def delete_request(
    session: Session,
    request_id: int,
    current_user: User,
):
    request = get_request(session, request_id, current_user)

    if request.group_id is not None:
        group = session.get(Group, request.group_id)

        if group is None:
            raise HTTPException(
                status_code=404,
                detail="Service request not found.",
            )

        if group.is_archived:
            raise HTTPException(
                status_code=400,
                detail="Group is archived. All modifications are blocked.",
            )

        if group.owner_id != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="Only the group owner can delete group service requests.",
            )

        if request.status != "pending":
            raise HTTPException(
                status_code=403,
                detail="You can only delete pending requests.",
            )

    elif current_user.role == STUDENT:
        if request.status != "pending":
            raise HTTPException(
                status_code=403,
                detail="You can only delete pending requests.",
            )

    elif current_user.role != ADMIN:
        raise HTTPException(
            status_code=403,
            detail="You are not allowed to delete this request.",
        )

    repository.delete_request(session, request)

    return {
        "message": "Service request deleted successfully.",
        "id": request_id,
    }


def assign_staff(
    session: Session,
    request_id: int,
    data: schemas.AssignStaffRequest,
    current_user: User,
):
    request = session.get(ServiceRequest, request_id)

    if request is None:
        raise HTTPException(
            status_code=404,
            detail="Service request not found.",
        )

    if request.group_id is not None:
        group = session.get(Group, request.group_id)

        if group is None:
            raise HTTPException(
                status_code=404,
                detail="Service request not found.",
            )

        is_owner = group.owner_id == current_user.id

        member = None
        if not is_owner:
            member = session.exec(
                select(GroupMember).where(
                    GroupMember.group_id == group.id,
                    GroupMember.user_id == current_user.id,
                )
            ).first()

        if not is_owner and member is None:
            raise HTTPException(
                status_code=404,
                detail="Service request not found.",
            )

        if not is_owner and not member.can_assign_requests:
            raise HTTPException(
                status_code=403,
                detail="You do not have permission to assign requests in this group.",
            )

        if group.is_archived:
            raise HTTPException(
                status_code=400,
                detail="Group is archived. All modifications are blocked.",
            )

    else:
        require_user_role(current_user, ADMIN)

    if request.status in ["resolved", "cancelled"]:
        raise HTTPException(
            status_code=400,
            detail="Cannot assign a completed or cancelled request.",
        )

    try:
        staff_id = UUID(data.staff_id)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid staff ID.",
        )

    staff_member = session.get(User, staff_id)

    if staff_member is None or staff_member.role != STAFF:
        raise HTTPException(
            status_code=400,
            detail="Selected user is not a valid staff member.",
        )

    request.assigned_to = staff_member.id
    request.status = "assigned"
    request.updated_at = datetime.now(timezone.utc)

    return repository.update_request(session, request)


def unassign_staff(
    session: Session,
    request_id: int,
    current_user: User,
):
    request = session.get(ServiceRequest, request_id)

    if request is None:
        raise HTTPException(
            status_code=404,
            detail="Service request not found.",
        )

    if request.group_id is not None:
        group = session.get(Group, request.group_id)

        if group is None:
            raise HTTPException(
                status_code=404,
                detail="Service request not found.",
            )

        is_owner = group.owner_id == current_user.id

        member = None
        if not is_owner:
            member = session.exec(
                select(GroupMember).where(
                    GroupMember.group_id == group.id,
                    GroupMember.user_id == current_user.id,
                )
            ).first()

        if not is_owner and member is None:
            raise HTTPException(
                status_code=404,
                detail="Service request not found.",
            )

        if not is_owner and not member.can_assign_requests:
            raise HTTPException(
                status_code=403,
                detail="You do not have permission to unassign requests in this group.",
            )

        if group.is_archived:
            raise HTTPException(
                status_code=400,
                detail="Group is archived. All modifications are blocked.",
            )

    else:
        require_user_role(current_user, ADMIN)

    if request.status in ["resolved", "cancelled"]:
        raise HTTPException(
            status_code=400,
            detail="Cannot unassign a completed or cancelled request.",
        )

    request.assigned_to = None
    request.status = "pending"
    request.updated_at = datetime.now(timezone.utc)

    return repository.update_request(session, request)
