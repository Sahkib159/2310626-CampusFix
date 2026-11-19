
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlmodel import Session, select

from database import get_session
from app.models.user import User
from app.auth.dependencies import get_current_admin


router = APIRouter(
    prefix="/api/staff",
    tags=["Staff Management"],
)


class StaffResponse(BaseModel):
    id: UUID
    name: str
    email: str
    role: str


@router.get(
    "",
    response_model=list[StaffResponse],
)
def get_all_staff(
    session: Session = Depends(get_session),
    current_admin: User = Depends(get_current_admin),
) -> list[User]:

    statement = (
        select(User)
        .where(User.role == "STAFF")
        .order_by(User.name)
    )

    return list(session.exec(statement).all())
