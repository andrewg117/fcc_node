from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import uvicorn

from api.routes.server import router as server_router
from core.exceptions import HttpError

app = FastAPI()

@app.exception_handler(HttpError)
async def http_error_handler(request: Request, exc: HttpError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": exc.status_code, "type": "HttpError", "message": exc.message},
    )


app.include_router(server_router)



if __name__ == "__main__":
    uvicorn.run("main:app", port=8001, reload=True)
