
import hashlib
import hmac
import os

from pwdlib import PasswordHash


password_hasher = PasswordHash.recommended()

# New password hashes use this explicit version marker.
PEPPER_VERSION_PREFIX = "pepper-v1$"


def _get_pepper() -> str:
    """Return the configured password pepper."""
    pepper = os.getenv("PASSWORD_PEPPER")

    if not pepper:
        raise RuntimeError(
            "PASSWORD_PEPPER is missing from the environment."
        )

    return pepper


def _prepare_password(password: str, pepper: str) -> str:
    """Pre-hash a password using HMAC-SHA256 and the server-side pepper."""
    return hmac.new(
        pepper.encode("utf-8"),
        password.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def hash_password(password: str) -> str:
    """Create a new Argon2 password hash using the server-side pepper."""
    pepper = _get_pepper()
    prepared_password = _prepare_password(password, pepper)

    return (
        PEPPER_VERSION_PREFIX
        + password_hasher.hash(prepared_password)
    )


def verify_password(
    plain_password: str,
    hashed_password: str,
) -> bool:
    """
    Verify both new peppered hashes and existing legacy Argon2 hashes.

    Legacy hashes remain verifiable so existing users are not locked out.
    """
    if hashed_password.startswith(PEPPER_VERSION_PREFIX):
        pepper = _get_pepper()
        stored_hash = hashed_password[len(PEPPER_VERSION_PREFIX):]

        prepared_password = _prepare_password(
            plain_password,
            pepper,
        )

        return password_hasher.verify(
            prepared_password,
            stored_hash,
        )

    # Backward compatibility for hashes created before pepper support.
    return password_hasher.verify(
        plain_password,
        hashed_password,
    )


def needs_password_upgrade(hashed_password: str) -> bool:
    """Identify legacy hashes that should be upgraded after login."""
    return not hashed_password.startswith(PEPPER_VERSION_PREFIX)
