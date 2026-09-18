from fastapi import APIRouter, status
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

from backend.core.exceptions import HttpError

router = APIRouter(prefix="/auth")

@router.post("/register")
async def register_user():
    return PlainTextResponse("Server home\n")


@router.post("/login")
async def login_user():
    return PlainTextResponse("Server home\n")