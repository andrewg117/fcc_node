from fastapi import APIRouter, status
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

from backend.core.exceptions import HttpError

router = APIRouter(prefix="/server")

@router.get("/")
async def home():
    return PlainTextResponse("Server home\n")