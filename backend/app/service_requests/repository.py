
from sqlmodel import Session, select

from app.models.service_request import ServiceRequest
from app.models.group import Group, GroupMember


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
        # Personal service requests only: excludes shared group requests
        statement = statement.where(
            ServiceRequest.user_id == user_id,
            ServiceRequest.group_id.is_(None),
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
        # Allow access if it is user's personal request, or if user is owner/member of the group
        member_group_ids = select(GroupMember.group_id).where(
            GroupMember.user_id == user_id
        )
        owned_group_ids = select(Group.id).where(
            Group.owner_id == user_id
        )
        statement = statement.where(
            (
                (ServiceRequest.user_id == user_id)
                & (ServiceRequest.group_id.is_(None))
            )
            | (ServiceRequest.group_id.in_(owned_group_ids))
            | (ServiceRequest.group_id.in_(member_group_ids))
        )

    elif role == "STAFF":
        # Staff access is strictly scoped to assigned requests
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
