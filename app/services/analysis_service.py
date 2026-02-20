from typing import Dict, Any, List, Tuple, Optional

from sqlalchemy import select, func, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.submission import Submission
from app.models.problem import Problem


async def compute_tag_accuracy(user_id: int, db: AsyncSession) -> Dict[str, Dict[str, Any]]:
    """Group submissions by tag and compute solved/attempted ratio per tag.

    Returns a mapping: tag -> {attempted:int, solved:int, accuracy:float}
    Uses SQL aggregation with unnest to avoid Python loops.
    """
    # resolve user's handle
    q = await db.execute(select(User.handle).where(User.id == user_id))
    handle = q.scalar_one_or_none()
    if not handle:
        return {}

    # use SQL aggregation with unnest to expand array tags and group by individual tag
    stmt = (
        select(
            func.unnest(Problem.tags).label("tag"),
            func.count(Submission.id).label("attempted"),
            func.sum(case(((Submission.verdict == "OK", 1)), else_=0)).label("solved"),
        )
        .join(Problem, (Submission.problem_contest_id == Problem.contest_id) & (Submission.problem_index == Problem.index))
        .where(Submission.author_handle == handle)
        .group_by("tag")
    )

    res = await db.execute(stmt)
    rows = res.fetchall()

    result: Dict[str, Dict[str, Any]] = {}
    for tag, attempted, solved in rows:
        attempted = int(attempted)
        solved = int(solved or 0)
        accuracy = solved / attempted if attempted else 0.0
        result[tag] = {"attempted": attempted, "solved": solved, "accuracy": accuracy}

    return result


async def compute_rating_bucket_accuracy(user_id: int, db: AsyncSession) -> Dict[str, Dict[str, Any]]:
    """Group problems into rating buckets and return success rate per bucket.

    Buckets are 800-1000, 1000-1200, ... up to 3000+.
    Returns mapping bucket_label -> {attempted, solved, success_rate}
    """
    q = await db.execute(select(User.handle).where(User.id == user_id))
    handle = q.scalar_one_or_none()
    if not handle:
        return {}

    # define bucket case expression
    buckets: List[Tuple[int, int]] = [(r, r + 200) for r in range(800, 3000, 200)]
    when_clauses = []
    for low, high in buckets:
        label = f"{low}-{high}"
        when_clauses.append(( (Problem.rating >= low) & (Problem.rating < high), label))
    when_clauses.append((Problem.rating >= 3000, "3000+"))

    bucket_case = case(when_clauses, else_="unknown")

    stmt = (
        select(
            bucket_case.label("bucket"),
            func.count(Submission.id).label("attempted"),
            func.sum(case(((Submission.verdict == "OK", 1)), else_=0)).label("solved"),
        )
        .join(Problem, (Submission.problem_contest_id == Problem.contest_id) & (Submission.problem_index == Problem.index))
        .where(Submission.author_handle == handle)
        .group_by(bucket_case)
    )

    res = await db.execute(stmt)
    rows = res.fetchall()

    result: Dict[str, Dict[str, Any]] = {}
    for bucket, attempted, solved in rows:
        attempted = int(attempted)
        solved = int(solved or 0)
        success_rate = solved / attempted if attempted else 0.0
        result[bucket] = {"attempted": attempted, "solved": solved, "success_rate": success_rate}

    return result


async def compute_average_solve_time(user_id: int, db: AsyncSession) -> Optional[float]:
    """Consider only Accepted submissions (verdict == 'OK') and compute average time_consumed_ms."""
    q = await db.execute(select(User.handle).where(User.id == user_id))
    handle = q.scalar_one_or_none()
    if not handle:
        return None

    stmt = (
        select(func.avg(Submission.time_consumed_ms))
        .where(Submission.author_handle == handle)
        .where(Submission.verdict == "OK")
    )
    res = await db.execute(stmt)
    avg_val = res.scalar_one_or_none()
    return float(avg_val) if avg_val is not None else None
