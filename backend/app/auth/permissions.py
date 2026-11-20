
from fastapi import HTTPException, status

from app.models.user import User


# Available application roles
STUDENT = "STUDENT"
STAFF = "STAFF"
ADMIN = "ADMIN"

ALL_ROLES = frozenset({
    STUDENT,
    STAFF,
    ADMIN,
})


def require_user_role(
    current_user: User,
    *allowed_roles: str,
) -> User:
    """
    Verify that the current user has one of the allowed roles.

    Returns the user when authorized.
    Raises HTTP 403 when access is denied.
    """

    if not allowed_roles:
        raise ValueError("At least one allowed role must be provided.")

    if current_user.role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to perform this action.",
        )

    return current_user
