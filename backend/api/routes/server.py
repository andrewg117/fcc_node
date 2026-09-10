from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

from core.exceptions import HttpError

router = APIRouter(prefix="/server")

@router.get("/")
async def home():
    return PlainTextResponse("Server home\n")

@router.get("/user/{user_id}")
async def get_user(user_id: str):
    if not user_id.isdigit():
        raise HttpError("Id given is not a number", 404)
    return PlainTextResponse(f"User ID: {int(user_id)}")