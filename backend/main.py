from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
from dotenv import load_dotenv

load_dotenv()

from api.routes.server import router as server_router
from core.exceptions import HttpError

environment: str = os.getenv("ENVIRONMENT") or "development"

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(os.getenv("CLIENT_URL"))],  # the client's dev origin; add the real prod origin once deployed
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

if __name__ == "__main__":
    port: str = os.getenv("SERVER_PORT") or "8001"

    if environment == "development":
        uvicorn.run("main:app", port=int(port), reload=True)
    else:
        uvicorn.run("main:app", port=int(port))


