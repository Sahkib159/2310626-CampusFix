
import csv
import io
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from sqlmodel import Session

from database import get_session
from app.auth.dependencies import get_current_admin
from app.models.user import User
from app.audit import service
from app.audit.service import record_event
from app.audit.schemas import AuditLogListResponse


router = APIRouter(
    prefix="/api/admin/audit-logs",
    tags=["Admin Audit Logs"],
)


def validate_date_range(
    start_date: datetime | None,
    end_date: datetime | None,
) -> None:
    if start_date and end_date and start_date > end_date:
        raise HTTPException(
            status_code=400,
            detail="start_date cannot be later than end_date.",
        )


@router.get("", response_model=AuditLogListResponse)
def get_audit_logs(
    action: str | None = Query(default=None, max_length=100),
    email: str | None = Query(default=None, max_length=255),
    actor_id: UUID | None = None,
    target_user_id: UUID | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    current_admin: User = Depends(get_current_admin),
    session: Session = Depends(get_session),
):
    validate_date_range(start_date, end_date)

    return service.list_audit_logs(
        session,
        action=action,
        email=email,
        actor_id=actor_id,
        target_user_id=target_user_id,
        start_date=start_date,
        end_date=end_date,
        page=page,
        page_size=page_size,
    )


@router.get("/export")
def export_audit_logs_csv(
    request: Request,
    action: str | None = Query(default=None, max_length=100),
    email: str | None = Query(default=None, max_length=255),
    actor_id: UUID | None = None,
    target_user_id: UUID | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    current_admin: User = Depends(get_current_admin),
    session: Session = Depends(get_session),
):
    validate_date_range(start_date, end_date)

    records = service.export_audit_logs(
        session,
        action=action,
        email=email,
        actor_id=actor_id,
        target_user_id=target_user_id,
        start_date=start_date,
        end_date=end_date,
    )

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "ID",
        "Actor ID",
        "Target User ID",
        "Action",
        "Email",
        "IP Address",
        "User Agent",
        "Details",
        "Created At",
    ])

    for record in records:
        writer.writerow([
            record.id,
            record.actor_id or "",
            record.target_user_id or "",
            record.action,
            record.email or "",
            record.ip_address,
            record.user_agent or "",
            record.details or "",
            record.created_at.isoformat(),
        ])

    record_event(
        session,
        "AUDIT_LOG_EXPORTED",
        request,
        actor_id=current_admin.id,
        details={"exported_records": len(records)},
    )

    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": (
                'attachment; filename="campusfix-audit-logs.csv"'
            )
        },
    )
