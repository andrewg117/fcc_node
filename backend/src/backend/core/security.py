import asyncio
from datetime import UTC, datetime, timedelta

import jwt
from pwdlib import PasswordHash

from backend.core.config import get_settings
from backend.core.exceptions import HttpError

_password_hash = PasswordHash.recommended()

# Checked against when the email is unknown, so a login attempt takes about
# as long whether or not the account exists.
_DUMMY_HASH = _password_hash.hash("not-a-real-password")


async def hash_password(password: str) -> str:
    # Argon2 is deliberately slow (CPU-bound). Run it in a worker thread so it
    # doesn't block the event loop for every other request.
    return await asyncio.to_thread(_password_hash.hash, password)


async def verify_password(password: str, password_hash: str | None) -> bool:
    valid = await asyncio.to_thread(_password_hash.verify, password, password_hash or _DUMMY_HASH)
    return valid and password_hash is not None


def create_access_token(user_id: str) -> str:
    settings = get_settings()
    now = datetime.now(UTC)
    payload = {
        "sub": user_id,
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_expire_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> str:
    """Return the user id stored in the token, or raise a 401 HttpError."""
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
            options={"require": ["exp", "sub"]},
        )
    except jwt.InvalidTokenError:
        raise HttpError("Invalid or expired token", 401) from None
    return payload["sub"]
