
import os
from ipaddress import ip_address

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlmodel import Session, select

from database import get_session

from app.models.user import User
from app.auth import schemas, service
from app.auth import config
from app.auth.config import (
    REFRESH_COOKIE_NAME,
    REFRESH_TOKEN_EXPIRE_DAYS,
    COOKIE_SAMESITE,
)
from app.auth.dependencies import (
    get_current_user,
    get_optional_current_user,
)
from app.audit.service import record_event


router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"],
)


def get_client_ip(request: Request) -> str:
    """
    Get the client's IP address.

    On Vercel, use the platform-provided X-Forwarded-For header.
    Locally, use the direct client address.

    The forwarded IP is validated before being used.
    """
    if os.getenv("VERCEL") == "1":
        forwarded_ip = request.headers.get("x-forwarded-for")

        try:
            first_ip = forwarded_ip.split(",")[0].strip()
            return str(ip_address(first_ip))
        except (ValueError, AttributeError):
            return "unknown"

    return (
        request.client.host
        if request.client is not None
        else "unknown"
    )


def set_refresh_cookie(
    response: Response,
    refresh_token: str,
) -> None:
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=refresh_token,
        httponly=True,
        secure=config.COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        path="/api/auth",
    )


@router.post(
    "/signup",
    response_model=schemas.TokenResponse,
    status_code=status.HTTP_201_CREATED,
)
def signup(
    data: schemas.SignupRequest,
    request: Request,
    response: Response,
    session: Session = Depends(get_session),
):
    try:
        result = service.signup(session, data)

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    user = session.exec(
        select(User).where(User.email == data.email)
    ).first()

    record_event(
        session,
        "ACCOUNT_REGISTERED",
        request,
        actor_id=user.id if user else None,
        target_user_id=user.id if user else None,
        email=data.email,
    )

    set_refresh_cookie(
        response,
        result["refresh_token"],
    )

    return result["response"]


@router.post(
    "/login",
    response_model=schemas.TokenResponse,
)
def login(
    data: schemas.LoginRequest,
    request: Request,
    response: Response,
    session: Session = Depends(get_session),
):
    client_ip = get_client_ip(request)

    try:
        result = service.login(
            session,
            data,
            client_ip,
        )

    except service.LoginRateLimitError as exc:
        record_event(
            session,
            "LOGIN_RATE_LIMITED",
            request,
            email=data.email,
            ip_address=client_ip,
            details={
                "reason": "Login rate limit exceeded",
            },
        )

        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(exc),
        )

    except ValueError as exc:
        record_event(
            session,
            "LOGIN_FAILED",
            request,
            email=data.email,
            ip_address=client_ip,
            details={
                "reason": "Invalid credentials or unavailable account",
            },
        )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        )

    user = session.exec(
        select(User).where(User.email == data.email)
    ).first()

    record_event(
        session,
        "LOGIN_SUCCESS",
        request,
        actor_id=user.id if user else None,
        target_user_id=user.id if user else None,
        email=data.email,
        ip_address=client_ip,
    )

    set_refresh_cookie(
        response,
        result["refresh_token"],
    )

    return result["response"]


@router.post(
    "/refresh",
    response_model=schemas.TokenResponse,
)
def refresh(
    request: Request,
    response: Response,
    session: Session = Depends(get_session),
):
    refresh_token = request.cookies.get(REFRESH_COOKIE_NAME)

    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token is missing.",
        )

    try:
        result = service.refresh_session(
            session,
            refresh_token,
        )

    except ValueError as exc:
        response.delete_cookie(
            key=REFRESH_COOKIE_NAME,
            path="/api/auth",
        )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        )

    set_refresh_cookie(
        response,
        result["refresh_token"],
    )

    return result["response"]


@router.post("/logout")
def logout(
    request: Request,
    response: Response,
    session: Session = Depends(get_session),
    current_user: User | None = Depends(get_optional_current_user),
):
    refresh_token = request.cookies.get(REFRESH_COOKIE_NAME)

    logout_user = service.logout(
        session,
        refresh_token,
        current_user,
    )

    # Never store refresh tokens in audit logs.
    # Record the user identity when either credential identifies them.
    record_event(
        session,
        "LOGOUT",
        request,
        actor_id=logout_user.id if logout_user else None,
        target_user_id=logout_user.id if logout_user else None,
        email=logout_user.email if logout_user else None,
    )

    response.delete_cookie(
        key=REFRESH_COOKIE_NAME,
        path="/api/auth",
    )

    return {
        "message": "Logged out successfully."
    }


@router.get(
    "/me",
    response_model=schemas.UserResponse,
)
def get_me(
    current_user: User = Depends(get_current_user),
):
    return schemas.UserResponse(
        id=str(current_user.id),
        name=current_user.name,
        email=current_user.email,
        role=current_user.role,
    )


@router.patch(
    "/me",
    response_model=schemas.UserResponse,
)
def update_me(
    data: schemas.ProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    try:
        updated_user = service.update_user_profile(
            session,
            current_user,
            data,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    return schemas.UserResponse(
        id=str(updated_user.id),
        name=updated_user.name,
        email=updated_user.email,
        role=updated_user.role,
    )


@router.post("/change-password")
def change_password(
    data: schemas.PasswordChangeRequest,
    request: Request,
    response: Response,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    try:
        service.change_user_password(
            session,
            current_user,
            data,
        )

    except ValueError as exc:
        if str(exc) == "Current password is incorrect.":
            record_event(
                session,
                "PASSWORD_CHANGE_FAILED",
                request,
                actor_id=current_user.id,
                target_user_id=current_user.id,
                email=current_user.email,
                ip_address=get_client_ip(request),
                details={
                    "reason": "Current password is incorrect.",
                },
            )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    record_event(
        session,
        "PASSWORD_CHANGED",
        request,
        actor_id=current_user.id,
        target_user_id=current_user.id,
        email=current_user.email,
    )

    response.delete_cookie(
        key=REFRESH_COOKIE_NAME,
        path="/api/auth",
    )

    return {
        "message": "Password changed successfully. Please log in again."
    }


@router.get("/sessions")
def get_sessions(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    return service.get_user_sessions(
        session,
        current_user.id,
    )


@router.delete("/sessions/{session_id}")
def revoke_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    try:
        return service.revoke_user_session(
            session,
            current_user.id,
            session_id,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
