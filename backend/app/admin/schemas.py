
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.audit.schemas import AuditLogResponse


class AdminUserResponse(BaseModel):
    id: UUID
    name: str
    email: str
    role: str
    is_active: bool
    is_banned: bool
    ban_reason: str | None
    banned_at: datetime | None
    banned_by: UUID | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AdminUserListResponse(BaseModel):
    users: list[AdminUserResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class BanUserRequest(BaseModel):
    reason: str = Field(
        min_length=3,
        max_length=500,
    )


class ChangeUserRoleRequest(BaseModel):
    role: str = Field(
        min_length=1,
        max_length=20,
    )


class AdminDashboardStatsResponse(BaseModel):
    total_users: int
    total_students: int
    total_staff: int
    total_admins: int
    active_users: int
    inactive_users: int
    banned_users: int


class RecentRegistrationResponse(BaseModel):
    id: UUID
    name: str
    email: str
    role: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AdminServiceRequestResponse(BaseModel):
    id: int
    title: str
    description: str
    category: str
    status: str
    assigned_to: UUID | None
    group_id: UUID | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AdminGroupMembershipResponse(BaseModel):
    id: UUID
    name: str
    description: str | None
    is_archived: bool
    is_owner: bool
    can_create_requests: bool
    can_edit_requests: bool
    can_assign_requests: bool
    created_at: datetime


class AdminSessionResponse(BaseModel):
    id: UUID
    created_at: datetime
    expires_at: datetime
    revoked_at: datetime | None
    is_active: bool


class AdminUserDetailResponse(BaseModel):
    user: AdminUserResponse
    service_requests: list[AdminServiceRequestResponse]
    groups: list[AdminGroupMembershipResponse]
    sessions: list[AdminSessionResponse]
    recent_activity: list[AuditLogResponse]
