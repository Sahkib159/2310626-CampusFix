from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlmodel import Session

from database import get_session
from app.auth.dependencies import get_current_user
from app.models.user import User
from app.schemas import ServiceRequestResponse
from app.groups import schemas, service

router = APIRouter(prefix="/api/groups", tags=["Shared Groups"])


@router.post(
    "",
    response_model=schemas.GroupResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_group(
    data: schemas.GroupCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> schemas.GroupResponse:
    return service.create_group(session, data, current_user)


@router.get("", response_model=list[schemas.GroupResponse])
def get_user_groups(
    include_archived: bool = Query(default=True),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> list[schemas.GroupResponse]:
    return service.get_user_groups(
        session,
        current_user,
        include_archived=include_archived,
    )


@router.get("/{group_id}", response_model=schemas.GroupResponse)
def get_group(
    group_id: UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> schemas.GroupResponse:
    return service.get_group_details(session, group_id, current_user)


@router.patch("/{group_id}", response_model=schemas.GroupResponse)
def update_group(
    group_id: UUID,
    data: schemas.GroupUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> schemas.GroupResponse:
    return service.update_group(session, group_id, data, current_user)


@router.post("/{group_id}/archive", response_model=schemas.GroupResponse)
def archive_group(
    group_id: UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> schemas.GroupResponse:
    return service.archive_group(session, group_id, current_user)


@router.post("/{group_id}/unarchive", response_model=schemas.GroupResponse)
def unarchive_group(
    group_id: UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> schemas.GroupResponse:
    return service.unarchive_group(session, group_id, current_user)


@router.delete("/{group_id}")
def delete_group(
    group_id: UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> dict[str, str]:
    return service.delete_group(session, group_id, current_user)


# GROUP MEMBERS


@router.get("/{group_id}/members", response_model=list[schemas.GroupMemberResponse])
def get_group_members(
    group_id: UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> list[schemas.GroupMemberResponse]:
    return service.get_group_members(session, group_id, current_user)


@router.post(
    "/{group_id}/members",
    response_model=schemas.GroupMemberResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_group_member(
    group_id: UUID,
    data: schemas.MemberAddRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> schemas.GroupMemberResponse:
    return service.add_group_member(session, group_id, data, current_user)


@router.patch(
    "/{group_id}/members/{user_id}",
    response_model=schemas.GroupMemberResponse,
)
def update_group_member_permissions(
    group_id: UUID,
    user_id: UUID,
    data: schemas.MemberUpdateRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> schemas.GroupMemberResponse:
    return service.update_group_member_permissions(
        session,
        group_id,
        user_id,
        data,
        current_user,
    )


@router.delete("/{group_id}/members/{user_id}")
def remove_group_member(
    group_id: UUID,
    user_id: UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> dict[str, str]:
    return service.remove_group_member(
        session,
        group_id,
        user_id,
        current_user,
    )


# GROUP SERVICE REQUESTS


@router.get("/{group_id}/requests", response_model=list[ServiceRequestResponse])
def get_group_requests(
    group_id: UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return service.get_group_requests(session, group_id, current_user)


@router.post(
    "/{group_id}/requests",
    response_model=ServiceRequestResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_group_request(
    group_id: UUID,
    data: schemas.GroupServiceRequestCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return service.create_group_request(session, group_id, data, current_user)


@router.get(
    "/{group_id}/requests/{request_id}",
    response_model=ServiceRequestResponse,
)
def get_group_request(
    group_id: UUID,
    request_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return service.get_group_request(
        session,
        group_id,
        request_id,
        current_user,
    )


@router.put(
    "/{group_id}/requests/{request_id}",
    response_model=ServiceRequestResponse,
)
def update_group_request(
    group_id: UUID,
    request_id: int,
    data: schemas.GroupServiceRequestUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return service.update_group_request(
        session,
        group_id,
        request_id,
        data,
        current_user,
    )


@router.delete("/{group_id}/requests/{request_id}")
def delete_group_request(
    group_id: UUID,
    request_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return service.delete_group_request(
        session,
        group_id,
        request_id,
        current_user,
    )


@router.patch(
    "/{group_id}/requests/{request_id}/assign",
    response_model=ServiceRequestResponse,
)
def assign_group_request_staff(
    group_id: UUID,
    request_id: int,
    data: schemas.GroupAssignStaffRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return service.assign_group_request_staff(
        session,
        group_id,
        request_id,
        data,
        current_user,
    )


@router.delete(
    "/{group_id}/requests/{request_id}/assign",
    response_model=ServiceRequestResponse,
)
def unassign_group_request_staff(
    group_id: UUID,
    request_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return service.unassign_group_request_staff(
        session,
        group_id,
        request_id,
        current_user,
    )
