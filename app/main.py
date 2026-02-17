from fastapi import FastAPI

from app.core.config import get_settings
from app.routers.health import router as health_router
from app.utils.logging import setup_logging

settings = get_settings()

# configure structured logging early
setup_logging()

app = FastAPI(title=settings.PROJECT_NAME)
app.include_router(health_router)


@app.get("/", tags=["root"])
async def root() -> dict:
    """Simple async root/health endpoint (no DB calls here)."""
    return {"status": "ok", "project": settings.PROJECT_NAME}
