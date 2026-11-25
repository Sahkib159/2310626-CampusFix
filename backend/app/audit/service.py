
import json
import math
from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import HTTPException, Request
from sqlmodel import Session

from app.auth.normalization import normalize_email
from app.audit.repository import (
    create_audit_log,
    get_audit_logs,
    get_audit_logs_for_export,
    get_security_audit_event_rows,
    get_security_audit_events,
)
from app.audit.schemas import (
    AuditLogListResponse,
    AuditLogResponse,
    SecurityAuditEventResponse,
    SecurityDashboardResponse,
    SecurityEmailSummary,
    SecurityIpSummary,
)
from app.models.audit_log import AuditLog

SECURITY_DASHBOARD_MAX_RANGE_DAYS = 90
SECURITY_REPEAT_WINDOW = timedelta(minutes=15)
SECURITY_REPEAT_EMAIL_THRESHOLD = 5
SECURITY_REPEAT_IP_THRESHOLD = 20


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
    ip_address: str | None = None,
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
        ip_address=ip_address or get_request_ip(request),
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


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)

    return value.astimezone(timezone.utc)


def resolve_security_date_range(
    start_date: datetime | None,
    end_date: datetime | None,
    *,
    now: datetime | None = None,
) -> tuple[datetime, datetime]:
    current_time = _as_utc(now or datetime.now(timezone.utc))
    effective_end = _as_utc(end_date) if end_date else current_time
    effective_start = (
        _as_utc(start_date)
        if start_date
        else effective_end - timedelta(days=7)
    )

    if effective_start > effective_end:
        raise HTTPException(
            status_code=400,
            detail="start_date cannot be later than end_date.",
        )

    range_days = (effective_end.date() - effective_start.date()).days + 1
    if range_days > SECURITY_DASHBOARD_MAX_RANGE_DAYS:
        raise HTTPException(
            status_code=400,
            detail=(
                "The security dashboard date range cannot exceed "
                f"{SECURITY_DASHBOARD_MAX_RANGE_DAYS} days."
            ),
        )

    return effective_start, effective_end


def _has_repeated_failures(
    timestamps: list[datetime],
    threshold: int,
    start_date: datetime,
) -> bool:
    ordered = sorted(_as_utc(timestamp) for timestamp in timestamps)
    left = 0

    for right, timestamp in enumerate(ordered):
        while timestamp - ordered[left] > SECURITY_REPEAT_WINDOW:
            left += 1

        if (
            timestamp >= start_date
            and right - left + 1 >= threshold
        ):
            return True

    return False


def _event_reason(details: str | None) -> str | None:
    if not details:
        return None

    try:
        parsed_details = json.loads(details)
    except json.JSONDecodeError:
        return details

    if isinstance(parsed_details, dict):
        reason = parsed_details.get("reason")
        if isinstance(reason, str):
            return reason

    return details


def get_security_dashboard(
    session: Session,
    *,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    page: int = 1,
    page_size: int = 50,
) -> SecurityDashboardResponse:
    effective_start, effective_end = resolve_security_date_range(
        start_date,
        end_date,
    )

    records, total = get_security_audit_events(
        session,
        start_date=effective_start,
        end_date=effective_end,
        offset=(page - 1) * page_size,
        limit=page_size,
    )

    summary_rows = get_security_audit_event_rows(
        session,
        start_date=effective_start - SECURITY_REPEAT_WINDOW,
        end_date=effective_end,
    )

    ip_groups: dict[str, dict] = {}
    email_groups: dict[str, dict] = {}
    ip_failure_times: dict[str, list[datetime]] = {}
    email_failure_times: dict[str, list[datetime]] = {}
    total_failed = 0
    total_rate_limited = 0

    for action, email, ip_address, created_at in summary_rows:
        occurred_at = _as_utc(created_at)
        normalized_email = normalize_email(email) if email else "unknown"
        normalized_ip = ip_address or "unknown"

        if action == "LOGIN_FAILED":
            ip_failure_times.setdefault(normalized_ip, []).append(occurred_at)
            email_failure_times.setdefault(
                normalized_email,
                [],
            ).append(occurred_at)

            if occurred_at < effective_start:
                continue

            total_failed += 1
            ip_group = ip_groups.setdefault(
                normalized_ip,
                {
                    "failed_count": 0,
                    "rate_limited_count": 0,
                    "last_failed_at": None,
                },
            )
            email_group = email_groups.setdefault(
                normalized_email,
                {
                    "failed_count": 0,
                    "rate_limited_count": 0,
                    "last_failed_at": None,
                },
            )
            ip_group["failed_count"] += 1
            email_group["failed_count"] += 1
            ip_group["last_failed_at"] = occurred_at
            email_group["last_failed_at"] = occurred_at

        elif effective_start <= occurred_at <= effective_end:
            total_rate_limited += 1
            ip_group = ip_groups.setdefault(
                normalized_ip,
                {
                    "failed_count": 0,
                    "rate_limited_count": 0,
                    "last_failed_at": None,
                },
            )
            email_group = email_groups.setdefault(
                normalized_email,
                {
                    "failed_count": 0,
                    "rate_limited_count": 0,
                    "last_failed_at": None,
                },
            )
            ip_group["rate_limited_count"] += 1
            email_group["rate_limited_count"] += 1

    by_ip = [
        SecurityIpSummary(
            ip_address=ip_address,
            failed_count=group["failed_count"],
            rate_limited_count=group["rate_limited_count"],
            repeated=(
                ip_address != "unknown"
                and _has_repeated_failures(
                    ip_failure_times.get(ip_address, []),
                    SECURITY_REPEAT_IP_THRESHOLD,
                    effective_start,
                )
            ),
            last_failed_at=group["last_failed_at"],
        )
        for ip_address, group in ip_groups.items()
    ]
    by_email = [
        SecurityEmailSummary(
            email=email,
            failed_count=group["failed_count"],
            rate_limited_count=group["rate_limited_count"],
            repeated=_has_repeated_failures(
                email_failure_times.get(email, []),
                SECURITY_REPEAT_EMAIL_THRESHOLD,
                effective_start,
            ),
            last_failed_at=group["last_failed_at"],
        )
        for email, group in email_groups.items()
    ]
    by_ip.sort(
        key=lambda item: (-item.failed_count, item.ip_address)
    )
    by_email.sort(
        key=lambda item: (-item.failed_count, item.email)
    )

    return SecurityDashboardResponse(
        start_date=effective_start,
        end_date=effective_end,
        total_failed=total_failed,
        total_rate_limited=total_rate_limited,
        by_ip=by_ip,
        by_email=by_email,
        events=[
            SecurityAuditEventResponse(
                id=record.id,
                action=record.action,
                email=(
                    normalize_email(record.email)
                    if record.email
                    else None
                ),
                ip_address=record.ip_address,
                created_at=_as_utc(record.created_at),
                reason=_event_reason(record.details),
            )
            for record in records
        ],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=math.ceil(total / page_size) if total else 0,
    )
