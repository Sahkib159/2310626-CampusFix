
from datetime import datetime, timezone
from typing import Optional

from sqlmodel import SQLModel, Field


class ServiceRequest(SQLModel, table=True):
    __tablename__ = "service_requests"

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(max_length=150)
    description: str
    category: str = Field(max_length=100)
    status: str = Field(default="pending", max_length=30)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
