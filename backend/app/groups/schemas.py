from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator


class GroupPermissions(BaseModel):
    can_create_requests: bool = False
    can_edit_requests: bool = False
    can_assign_requests: bool = False


class GroupCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    description: Optional[str] = Field(default=None, max_length=1000)

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        value = value.strip()
        if len(value) < 2:
            raise ValueError("Group name must contain at least 2 characters.")
        return value


class GroupUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=100)
    description: Optional[str] = Field(default=None, max_length=1000)

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: Optional[str]) -> Optional[str]:
        if value is not None:
            value = value.strip()
            if len(value) < 2:
                raise ValueError("Group name must contain at least 2 characters.")
        return value


class GroupResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str] = None
    owner_id: UUID
    is_archived: bool = False
    created_at: datetime
    updated_at: datetime
    is_owner: bool = False
    permissions: Optional[GroupPermissions] = None


class MemberAddRequest(BaseModel):
    email: EmailStr
    can_create_requests: bool = False
    can_edit_requests: bool = False
    can_assign_requests: bool = False

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> EmailStr:
        return value.strip().lower()


class MemberUpdateRequest(BaseModel):
    can_create_requests: Optional[bool] = None
    can_edit_requests: Optional[bool] = None
    can_assign_requests: Optional[bool] = None


class GroupMemberResponse(BaseModel):
    id: UUID
    group_id: UUID
    user_id: UUID
    user_name: str
    user_email: str
    role: str  # "OWNER" | "MEMBER"
    is_owner: bool = False
    can_create_requests: bool = False
    can_edit_requests: bool = False
    can_assign_requests: bool = False
    created_at: datetime


class GroupServiceRequestCreate(BaseModel):
    title: str = Field(min_length=3, max_length=150)
    description: str = Field(min_length=5)
    category: str = Field(min_length=2, max_length=100)


class GroupServiceRequestUpdate(BaseModel):
    # Restricted fields only: cannot modify user_id, group_id, assigned_to or status
    title: str = Field(min_length=3, max_length=150)
    description: str = Field(min_length=5)
    category: str = Field(min_length=2, max_length=100)


class GroupAssignStaffRequest(BaseModel):
    staff_id: str = Field(min_length=1)
