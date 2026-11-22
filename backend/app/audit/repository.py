
from datetime import datetime
from uuid import UUID

from sqlmodel import Session, select, func

from app.models.audit_log import AuditLog


def create_audit_log(
    session: Session,
    audit_log: AuditLog,
) -> AuditLog:
    session.add(audit_log)
    session.commit()
    session.refresh(audit_log)
    return audit_log


def get_audit_logs(
    session: Session,
    *,
    action: str | None = None,
    email: str | None = None,
    actor_id: UUID | None = None,
    target_user_id: UUID | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    offset: int = 0,
    limit: int = 50,
) -> tuple[list[AuditLog], int]:
    statement = select(AuditLog)

    if action:
        statement = statement.where(AuditLog.action == action)

    if email:
        statement = statement.where(
            AuditLog.email.ilike(f"%{email.strip()}%")
        )

    if actor_id:
        statement = statement.where(AuditLog.actor_id == actor_id)

    if target_user_id:
        statement = statement.where(
            AuditLog.target_user_id == target_user_id
        )

    if start_date:
        statement = statement.where(
            AuditLog.created_at >= start_date
        )

    if end_date:
        statement = statement.where(
            AuditLog.created_at <= end_date
        )

    count_statement = (
        select(func.count())
        .select_from(statement.subquery())
    )

    total = session.exec(count_statement).one()

    records_statement = (
        statement
        .order_by(AuditLog.created_at.desc())
        .offset(offset)
        .limit(limit)
    )

    records = list(session.exec(records_statement).all())

    return records, total


def get_audit_logs_for_export(
    session: Session,
    *,
    action: str | None = None,
    email: str | None = None,
    actor_id: UUID | None = None,
    target_user_id: UUID | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    limit: int = 10000,
) -> list[AuditLog]:
    records, _ = get_audit_logs(
        session,
        action=action,
        email=email,
        actor_id=actor_id,
        target_user_id=target_user_id,
        start_date=start_date,
        end_date=end_date,
        offset=0,
        limit=limit,
    )

    return records
