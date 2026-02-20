from time import perf_counter
import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from datetime import datetime

from app.core.config import get_settings
from app.routers.health import router as health_router
from app.utils.logging import setup_logging
from app.clients.codeforces import make_codeforces_client

settings = get_settings()

# configure structured logging early
setup_logging()
logger = logging.getLogger("app.middleware")

app = FastAPI(title=settings.PROJECT_NAME)
app.include_router(health_router)


@app.on_event("startup")
async def _startup_codeforces_client() -> None:
    # initialize and attach a reusable Codeforces Async client to app state
    app.state.codeforces_client = make_codeforces_client()


@app.on_event("shutdown")
async def _shutdown_codeforces_client() -> None:
    c = getattr(app.state, "codeforces_client", None)
    if c is not None:
        # close the client via its public API
        await c.close()


@app.exception_handler(IntegrityError)
async def integrity_error_handler(request: Request, exc: IntegrityError) -> JSONResponse:
    logger.exception("IntegrityError on request %s %s", request.method, request.url.path)
    body = {
        "error": "IntegrityError",
        "detail": str(exc.orig) if getattr(exc, "orig", None) is not None else str(exc),
        "path": request.url.path,
        "status_code": 400,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
    return JSONResponse(status_code=400, content=body)


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled exception on request %s %s", request.method, request.url.path)
    body = {
        "error": "InternalServerError",
        "detail": "An unexpected error occurred.",
        "path": request.url.path,
        "status_code": 500,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
    return JSONResponse(status_code=500, content=body)


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    start = perf_counter()
    response = await call_next(request)
    elapsed = (perf_counter() - start) * 1000.0
    logger.info(
        "request",
        extra={
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "elapsed_ms": round(elapsed, 2),
        },
    )
    return response


@app.get("/", tags=["root"])
async def root() -> dict:
    """Simple async root/health endpoint (no DB calls here)."""
    return {"status": "ok", "project": settings.PROJECT_NAME}
