
import os
from datetime import timedelta

from dotenv import load_dotenv


BACKEND_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))
    )
)

load_dotenv(os.path.join(BACKEND_DIR, ".env"))


# JWT configuration
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")

if not JWT_SECRET_KEY:
    raise RuntimeError(
        "JWT_SECRET_KEY is missing from backend/.env"
    )

JWT_ALGORITHM = "HS256"


# Access token: maximum lifetime is 15 minutes.
ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15")
)

if not 1 <= ACCESS_TOKEN_EXPIRE_MINUTES <= 15:
    raise RuntimeError(
        "ACCESS_TOKEN_EXPIRE_MINUTES must be between 1 and 15."
    )


# Refresh token configuration
REFRESH_TOKEN_EXPIRE_DAYS = int(
    os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7")
)


ACCESS_TOKEN_EXPIRE = timedelta(
    minutes=ACCESS_TOKEN_EXPIRE_MINUTES
)

REFRESH_TOKEN_EXPIRE = timedelta(
    days=REFRESH_TOKEN_EXPIRE_DAYS
)


# Refresh cookie configuration
REFRESH_COOKIE_NAME = "campusfix_refresh"

COOKIE_SECURE = (
    os.getenv("COOKIE_SECURE", "false").lower() == "true"
)

COOKIE_SAMESITE = os.getenv("COOKIE_SAMESITE", "lax")
