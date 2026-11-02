
from fastapi import APIRouter, Depends
from sqlmodel import Session

from backend.database import get_session
from backend.app import schemas
from backend.app.models.service_request import ServiceRequest
from backend.app.service_requests import service


router = APIRouter(
    prefix="/api/requests",
    tags=["Service Requests"],
)


@router.post(
    "",
    response_model=schemas.ServiceRequestResponse,
    status_code=201,
)
def create_request(
    data: schemas.ServiceRequestCreate,
    session: Session = Depends(get_session),
) -> ServiceRequest:
    return service.create_request(session, data)


@router.get(
    "",
    response_model=list[schemas.ServiceRequestResponse],
)
def get_all_requests(
    session: Session = Depends(get_session),
) -> list[ServiceRequest]:
    return service.get_all_requests(session)


@router.get(
    "/{request_id}",
    response_model=schemas.ServiceRequestResponse,
)
def get_request(
    request_id: int,
    session: Session = Depends(get_session),
) -> ServiceRequest:
    return service.get_request(session, request_id)


@router.put(
    "/{request_id}",
    response_model=schemas.ServiceRequestResponse,
)
def update_request(
    request_id: int,
    data: schemas.ServiceRequestUpdate,
    session: Session = Depends(get_session),
) -> ServiceRequest:
    return service.update_request(session, request_id, data)


@router.delete("/{request_id}")
def delete_request(
    request_id: int,
    session: Session = Depends(get_session),
) -> dict:
    return service.delete_request(session, request_id)
