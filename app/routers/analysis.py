from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio
import logging

from app.db.session import get_async_session, AsyncSessionLocal
from app.models.user import User
from app.services.codeforces_service import sync_user_submissions, CodeforcesAPIError
from app.services.analysis_service import (
    compute_tag_accuracy,
    compute_rating_bucket_accuracy,
    compute_average_solve_time,
)
from app.services.insights_service import generate_user_insights

router = APIRouter(prefix="/analysis", tags=["analysis"])
logger = logging.getLogger("app.routers.analysis")


async def _background_sync(handle: str) -> None:
    async with AsyncSessionLocal() as session:
        try:
            await sync_user_submissions(handle, session)
        except Exception as exc:  # noqa: BLE001 - log and swallow to avoid crashing
            logger.exception("background sync failed for %s: %s", handle, exc)


@router.get("/{handle}")
async def analyze_handle(handle: str, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_async_session)):
    """Trigger background sync of user submissions, compute analysis from DB, and return insights."""
    # find local User by handle
    q = await db.execute(select(User).where(User.handle == handle))
    user = q.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found. Register user with this handle first.")

    # schedule background sync to run after response is sent
    # use asyncio.create_task inside background task to schedule the coroutine
    background_tasks.add_task(asyncio.create_task, _background_sync(handle))

    # compute analysis from whatever data is currently in DB (sync runs asynchronously)
    tag_stats = await compute_tag_accuracy(user.id, db)
    rating_stats = await compute_rating_bucket_accuracy(user.id, db)
    avg_time = await compute_average_solve_time(user.id, db)

    insights = generate_user_insights(tag_stats, rating_stats, avg_time)

    return {
        "tag_accuracy": tag_stats,
        "rating_accuracy": rating_stats,
        "average_solve_time_ms": avg_time,
        "insights": insights,
    }
