from datetime import datetime, timezone

from fastapi import HTTPException
from sqlmodel import Session

from app import schemas
from app.models.service_request import ServiceRequest
from app.service_requests import repository


def create_request(
    session: Session,
    data: schemas.ServiceRequestCreate,
) -> ServiceRequest:
    new_request = ServiceRequest(
        title=data.title,
        description=data.description,
        category=data.category,
        status="pending",
    )

    return repository.create_request(session, new_request)


def get_all_requests(session: Session) -> list[ServiceRequest]:
    return repository.get_all_requests(session)


def get_request(
    session: Session,
    request_id: int,
) -> ServiceRequest:
    request = repository.get_request_by_id(session, request_id)

    if request is None:
        raise HTTPException(
            status_code=404,
            detail="Service request not found",
        )

    return request


def update_request(
    session: Session,
    request_id: int,
    data: schemas.ServiceRequestUpdate,
) -> ServiceRequest:
    request = get_request(session, request_id)

    request.title = data.title
    request.description = data.description
    request.category = data.category
    request.status = data.status
    request.updated_at = datetime.now(timezone.utc)

    return repository.update_request(session, request)


def delete_request(session: Session, request_id: int) -> dict:
    request = get_request(session, request_id)

    repository.delete_request(session, request)

    return {
        "message": "Service request deleted successfully",
        "id": request_id,
    }
