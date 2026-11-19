
from fastapi import APIRouter, Depends
from sqlmodel import Session

from database import get_session
from app import schemas
from app.models.service_request import ServiceRequest
from app.models.user import User
from app.auth.dependencies import get_current_user
from app.service_requests import service


router = APIRouter(prefix="/api/requests", tags=["Service Requests"])


@router.post("", response_model=schemas.ServiceRequestResponse, status_code=201)
def create_request(
    data: schemas.ServiceRequestCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> ServiceRequest:
    return service.create_request(session, data, current_user)


@router.get("", response_model=list[schemas.ServiceRequestResponse])
def get_all_requests(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> list[ServiceRequest]:
    return service.get_all_requests(session, current_user)


@router.get("/{request_id}", response_model=schemas.ServiceRequestResponse)
def get_request(
    request_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> ServiceRequest:
    return service.get_request(session, request_id, current_user)


@router.put("/{request_id}", response_model=schemas.ServiceRequestResponse)
def update_request(
    request_id: int,
    data: schemas.ServiceRequestUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> ServiceRequest:
    return service.update_request(session, request_id, data, current_user)


@router.delete("/{request_id}")
def delete_request(
    request_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return service.delete_request(session, request_id, current_user)


@router.patch("/{request_id}/assign", response_model=schemas.ServiceRequestResponse)
def assign_staff(
    request_id: int,
    data: schemas.AssignStaffRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> ServiceRequest:
    return service.assign_staff(session, request_id, data, current_user)


@router.delete("/{request_id}/assign", response_model=schemas.ServiceRequestResponse)
def unassign_staff(
    request_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> ServiceRequest:
    return service.unassign_staff(session, request_id, current_user)
