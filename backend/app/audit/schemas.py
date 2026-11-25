
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AuditLogResponse(BaseModel):
    id: UUID
    actor_id: UUID | None
    target_user_id: UUID | None
    action: str
    email: str | None
    ip_address: str
    user_agent: str | None
    details: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AuditLogListResponse(BaseModel):
    logs: list[AuditLogResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class SecurityAuditEventResponse(BaseModel):
    id: UUID
    action: str
    email: str | None
    ip_address: str
    created_at: datetime
    reason: str | None


class SecurityIpSummary(BaseModel):
    ip_address: str
    failed_count: int
    rate_limited_count: int
    repeated: bool
    last_failed_at: datetime | None


class SecurityEmailSummary(BaseModel):
    email: str
    failed_count: int
    rate_limited_count: int
    repeated: bool
    last_failed_at: datetime | None


class SecurityDashboardResponse(BaseModel):
    start_date: datetime
    end_date: datetime
    total_failed: int
    total_rate_limited: int
    by_ip: list[SecurityIpSummary]
    by_email: list[SecurityEmailSummary]
    events: list[SecurityAuditEventResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
