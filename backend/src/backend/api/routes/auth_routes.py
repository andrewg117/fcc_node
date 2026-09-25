from fastapi import APIRouter, status

from backend.api.deps import CurrentUser, UserRepo
from backend.core.exceptions import HttpError
from backend.core.security import create_access_token, hash_password, verify_password
from backend.repositories.user_repository import DuplicateEmailError
from backend.schemas.auth import (
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    RegisterResponse,
    UserPublic,
)

router = APIRouter(prefix="/auth")


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_user(body: RegisterRequest, users: UserRepo) -> RegisterResponse:
    password_hash = await hash_password(body.password)
    try:
        user = await users.create(body.name, body.email, password_hash)
    except DuplicateEmailError:
        raise HttpError("Email already registered", 409) from None

    return RegisterResponse(
        message="User created successfully",
        data=UserPublic(name=user.name, email=user.email),
    )


@router.post("/login")
async def login_user(body: LoginRequest, users: UserRepo) -> LoginResponse:
    user = await users.get_by_email(body.email)
    password_ok = await verify_password(
        body.password, user.password_hash if user else None
    )
    if user is None or not password_ok:
        raise HttpError("Invalid email or password", 401)

    return LoginResponse(
        message="Login successful",
        token=create_access_token(user.id),
        data=UserPublic(name=user.name, email=user.email),
    )


@router.get("/me")
async def read_current_user(user: CurrentUser) -> UserPublic:
    return UserPublic(name=user.name, email=user.email)
