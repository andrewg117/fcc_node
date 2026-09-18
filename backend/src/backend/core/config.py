import os
from dataclasses import dataclass
from functools import lru_cache


@dataclass(frozen=True)
class Settings:
    mongodb_uri: str
    mongodb_db_name: str
    jwt_secret: str
    jwt_algorithm: str
    access_token_expire_minutes: int


def _require(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


@lru_cache
def get_settings() -> Settings:
    jwt_secret = _require("JWT_SECRET")
    if len(jwt_secret) < 32:
        raise RuntimeError("JWT_SECRET must be at least 32 characters long")

    return Settings(
        mongodb_uri=_require("MONGODB_URI"),
        mongodb_db_name=os.getenv("MONGODB_DB_NAME") or "fcc_node",
        jwt_secret=jwt_secret,
        jwt_algorithm="HS256",
        access_token_expire_minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES") or "60"),
    )
