
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


RequestStatus = Literal[
    "pending",
    "assigned",
    "in_progress",
    "resolved",
    "cancelled",
]


class ServiceRequestCreate(BaseModel):
    title: str = Field(min_length=3, max_length=150)
    description: str = Field(min_length=5)
    category: str = Field(min_length=2, max_length=100)


class ServiceRequestUpdate(BaseModel):
    title: str = Field(min_length=3, max_length=150)
    description: str = Field(min_length=5)
    category: str = Field(min_length=2, max_length=100)
    status: RequestStatus


class ServiceRequestResponse(BaseModel):
    id: int
    user_id: UUID | None = None
    assigned_to: UUID | None = None
    title: str
    description: str
    category: str
    status: RequestStatus


class AssignStaffRequest(BaseModel):
    staff_id: str = Field(min_length=1)
