from uuid import UUID

from sqlalchemy import func
from sqlmodel import Session, select

from app.models.group import Group, GroupMember
from app.models.service_request import ServiceRequest
from app.models.user import User


def create_group(session: Session, group: Group) -> Group:
    session.add(group)
    session.commit()
    session.refresh(group)
    return group


def get_group_by_id(session: Session, group_id: UUID) -> Group | None:
    return session.get(Group, group_id)


def get_user_groups(
    session: Session,
    user_id: UUID,
    include_archived: bool = True,
) -> list[Group]:
    """
    Retrieve all groups where the user is either the owner or an accepted member.
    """
    member_group_ids = select(GroupMember.group_id).where(
        GroupMember.user_id == user_id
    )

    statement = select(Group).where(
        (Group.owner_id == user_id) | (Group.id.in_(member_group_ids))
    )

    if not include_archived:
        statement = statement.where(Group.is_archived.is_(False))

    statement = statement.order_by(Group.name)
    return list(session.exec(statement).all())


def update_group(session: Session, group: Group) -> Group:
    session.add(group)
    session.commit()
    session.refresh(group)
    return group


def delete_group(session: Session, group: Group) -> None:
    session.delete(group)
    session.commit()


def get_group_requests_count(session: Session, group_id: UUID) -> int:
    statement = (
        select(func.count())
        .select_from(ServiceRequest)
        .where(ServiceRequest.group_id == group_id)
    )
    return session.exec(statement).one()


def get_group_member(
    session: Session,
    group_id: UUID,
    user_id: UUID,
) -> GroupMember | None:
    statement = select(GroupMember).where(
        GroupMember.group_id == group_id,
        GroupMember.user_id == user_id,
    )
    return session.exec(statement).first()


def get_group_members_with_users(
    session: Session,
    group_id: UUID,
) -> list[tuple[GroupMember, User]]:
    statement = (
        select(GroupMember, User)
        .join(User, GroupMember.user_id == User.id)
        .where(GroupMember.group_id == group_id)
        .order_by(User.name)
    )
    return list(session.exec(statement).all())


def add_group_member(session: Session, member: GroupMember) -> GroupMember:
    session.add(member)
    session.commit()
    session.refresh(member)
    return member


def update_group_member(session: Session, member: GroupMember) -> GroupMember:
    session.add(member)
    session.commit()
    session.refresh(member)
    return member


def delete_group_member(session: Session, member: GroupMember) -> None:
    session.delete(member)
    session.commit()


def get_group_requests(
    session: Session,
    group_id: UUID,
) -> list[ServiceRequest]:
    statement = (
        select(ServiceRequest)
        .where(ServiceRequest.group_id == group_id)
        .order_by(ServiceRequest.created_at.desc())
    )
    return list(session.exec(statement).all())


def get_group_request_by_id(
    session: Session,
    group_id: UUID,
    request_id: int,
) -> ServiceRequest | None:
    statement = select(ServiceRequest).where(
        ServiceRequest.group_id == group_id,
        ServiceRequest.id == request_id,
    )
    return session.exec(statement).first()


def create_group_request(
    session: Session,
    request: ServiceRequest,
) -> ServiceRequest:
    session.add(request)
    session.commit()
    session.refresh(request)
    return request


def update_group_request(
    session: Session,
    request: ServiceRequest,
) -> ServiceRequest:
    session.add(request)
    session.commit()
    session.refresh(request)
    return request


def delete_group_request(
    session: Session,
    request: ServiceRequest,
) -> None:
    session.delete(request)
    session.commit()
