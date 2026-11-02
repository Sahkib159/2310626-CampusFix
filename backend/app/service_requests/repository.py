
from sqlmodel import Session, select

from backend.app.models.service_request import ServiceRequest


def create_request(
    session: Session,
    request: ServiceRequest,
) -> ServiceRequest:
    session.add(request)
    session.commit()
    session.refresh(request)
    return request


def get_all_requests(session: Session) -> list[ServiceRequest]:
    statement = select(ServiceRequest)
    return list(session.exec(statement).all())


def get_request_by_id(
    session: Session,
    request_id: int,
) -> ServiceRequest | None:
    return session.get(ServiceRequest, request_id)


def update_request(
    session: Session,
    request: ServiceRequest,
) -> ServiceRequest:
    session.add(request)
    session.commit()
    session.refresh(request)
    return request


def delete_request(
    session: Session,
    request: ServiceRequest,
) -> None:
    session.delete(request)
    session.commit()
