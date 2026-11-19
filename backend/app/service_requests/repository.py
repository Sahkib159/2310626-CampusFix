
from sqlmodel import Session, select

from app.models.service_request import ServiceRequest


def create_request(session: Session, request: ServiceRequest) -> ServiceRequest:
    session.add(request)
    session.commit()
    session.refresh(request)
    return request


def get_all_requests(
    session: Session,
    user_id,
    role: str,
) -> list[ServiceRequest]:
    statement = select(ServiceRequest)

    if role == "STUDENT":
        statement = statement.where(
            ServiceRequest.user_id == user_id
        )

    elif role == "STAFF":
        statement = statement.where(
            ServiceRequest.assigned_to == user_id
        )

    elif role == "ADMIN":
        pass

    else:
        return []

    return list(session.exec(statement).all())


def get_request_by_id(
    session: Session,
    request_id: int,
    user_id,
    role: str,
) -> ServiceRequest | None:
    statement = select(ServiceRequest).where(
        ServiceRequest.id == request_id
    )

    if role == "STUDENT":
        statement = statement.where(
            ServiceRequest.user_id == user_id
        )

    elif role == "STAFF":
        statement = statement.where(
            ServiceRequest.assigned_to == user_id
        )

    elif role == "ADMIN":
        pass

    else:
        return None

    return session.exec(statement).first()


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
