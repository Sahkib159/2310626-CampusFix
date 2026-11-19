
import hashlib
import secrets


def generate_refresh_token() -> str:
    """
    Generate a cryptographically secure random refresh token.
    """
    return secrets.token_urlsafe(48)


def hash_refresh_token(token: str) -> str:
    """
    Hash a refresh token using SHA-256 before database storage.
    """
    return hashlib.sha256(
        token.encode("utf-8")
    ).hexdigest()


def verify_refresh_token(
    token: str,
    stored_hash: str,
) -> bool:
    """
    Verify a refresh token against its stored hash.
    """
    return secrets.compare_digest(
        hash_refresh_token(token),
        stored_hash,
    )
