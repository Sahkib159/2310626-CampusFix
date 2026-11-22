
import json
import math
from datetime import datetime, timezone
from uuid import UUID

from fastapi import Request
from sqlmodel import Session

from app.audit.repository import (
    create_audit_log,
    get_audit_logs,
    get_audit_logs_for_export,
)
from app.audit.schemas import (
    AuditLogListResponse,
    AuditLogResponse,
)
from app.models.audit_log import AuditLog


def get_request_ip(request: Request | None) -> str:
    if request is None or request.client is None:
        return "unknown"

    return request.client.host or "unknown"


def get_user_agent(request: Request | None) -> str | None:
    if request is None:
        return None

    user_agent = request.headers.get("user-agent")

    if user_agent:
        return user_agent[:1000]

    return None


def record_event(
    session: Session,
    action: str,
    request: Request | None = None,
    *,
    actor_id: UUID | None = None,
    target_user_id: UUID | None = None,
    email: str | None = None,
    details: dict | str | None = None,
) -> AuditLog:
    if isinstance(details, dict):
        details_value = json.dumps(details, ensure_ascii=False)
    else:
        details_value = details

    audit_log = AuditLog(
        actor_id=actor_id,
        target_user_id=target_user_id,
        action=action,
        email=email,
        ip_address=get_request_ip(request),
        user_agent=get_user_agent(request),
        details=details_value,
        created_at=datetime.now(timezone.utc),
    )

    return create_audit_log(session, audit_log)


def list_audit_logs(
    session: Session,
    *,
    action: str | None = None,
    email: str | None = None,
    actor_id: UUID | None = None,
    target_user_id: UUID | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    page: int = 1,
    page_size: int = 50,
) -> AuditLogListResponse:
    records, total = get_audit_logs(
        session,
        action=action,
        email=email,
        actor_id=actor_id,
        target_user_id=target_user_id,
        start_date=start_date,
        end_date=end_date,
        offset=(page - 1) * page_size,
        limit=page_size,
    )

    return AuditLogListResponse(
        logs=[
            AuditLogResponse.model_validate(record)
            for record in records
        ],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=math.ceil(total / page_size) if total else 0,
    )


def export_audit_logs(
    session: Session,
    *,
    action: str | None = None,
    email: str | None = None,
    actor_id: UUID | None = None,
    target_user_id: UUID | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
) -> list[AuditLog]:
    return get_audit_logs_for_export(
        session,
        action=action,
        email=email,
        actor_id=actor_id,
        target_user_id=target_user_id,
        start_date=start_date,
        end_date=end_date,
    )
