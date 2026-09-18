from fastapi import APIRouter, status
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

from backend.core.exceptions import HttpError

router = APIRouter(prefix="/server")

@router.get("/")
async def home():
    return PlainTextResponse("Server home\n")

@router.get("/user/{user_id}")
async def get_user(user_id: str):
    if not user_id.isdigit():
        raise HttpError("Id given is not a number", 404)
    return PlainTextResponse(f"User ID: {int(user_id)}")

class User(BaseModel):
    name: str
    email: str

@router.post("/user", status_code=status.HTTP_201_CREATED)
async def create_user(user: User):
    user_data = user.model_dump()

    if not user.name or not user.email:
        raise HttpError("Fields missing. User not created", 422)
    return {"message": "User created successfully", "data": user_data}