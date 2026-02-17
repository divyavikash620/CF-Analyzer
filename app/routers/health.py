from fastapi import APIRouter

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/", summary="Health check")
async def health_check() -> dict:
    """Very small, dependency-free health endpoint (no DB access here)."""
    return {"status": "ok"}
