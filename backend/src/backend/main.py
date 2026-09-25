import os

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

load_dotenv()

from backend.api.routes.auth_routes import router as auth_router
from backend.api.routes.server_routes import router as server_router
from backend.core.exceptions import HttpError
from backend.db.postgres import lifespan

environment: str = os.getenv("ENVIRONMENT") or "development"

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        str(os.getenv("CLIENT_URL"))
    ],  # the client's dev origin; add the real prod origin once deployed
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(HttpError)
async def http_error_handler(request: Request, exc: HttpError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": exc.status_code, "type": "HttpError", "message": exc.message},
    )


app.include_router(server_router)
app.include_router(auth_router)


def run() -> None:
    port: str = os.getenv("SERVER_PORT") or "8001"

    if environment == "development":
        uvicorn.run("backend.main:app", port=int(port), reload=True)
    else:
        uvicorn.run("backend.main:app", port=int(port))
