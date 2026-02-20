import logging
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import select, update as sa_update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.clients.codeforces import make_codeforces_client, CodeforcesAPIError
from app.models.problem import Problem
from app.models.submission import Submission
from app.models.user import User

logger = logging.getLogger("app.services.codeforces")


def _submission_id(raw_submission: Dict[str, Any]) -> Optional[int]:
    sid = raw_submission.get("id") or raw_submission.get("submissionId")
    if sid is None:
        return None
    try:
        return int(sid)
    except (TypeError, ValueError):
        return None


async def sync_user_submissions(handle: str, db: AsyncSession, batch_size: int = 200) -> int:
    """Fetch and upsert new Codeforces submissions for a local user."""
    async with db.begin():
        user_row = (
            await db.execute(
                select(User.id, User.last_synced_submission_id).where(User.handle == handle)
            )
        ).first()

    if user_row is None:
        logger.warning("sync_user_submissions: user not found for handle=%s", handle)
        return 0

    user_id, last_synced_submission_id = user_row

    # Codeforces `from` is an offset, not a submission id. We fetch pages and stop
    # once we reach entries at or below the last synced submission id.
    page_size = 1000
    page_from = 1
    newest_seen_id = int(last_synced_submission_id) if last_synced_submission_id is not None else None
    fetched_new_submissions: List[Tuple[Dict[str, Any], int]] = []

    client = make_codeforces_client()
    try:
        while True:
            page_raw = await client.get_user_submissions(handle, from_=page_from, count=page_size)
            page = page_raw if isinstance(page_raw, list) else []
            if not page:
                break

            hit_previous_sync = False
            for submission in page:
                sid = _submission_id(submission)
                if sid is None:
                    continue

                if newest_seen_id is None or sid > newest_seen_id:
                    newest_seen_id = sid

                if last_synced_submission_id is None or sid > int(last_synced_submission_id):
                    fetched_new_submissions.append((submission, sid))
                else:
                    hit_previous_sync = True

            if hit_previous_sync or len(page) < page_size:
                break

            page_from += page_size
    except CodeforcesAPIError as exc:
        logger.error("failed to fetch submissions for %s: %s", handle, exc)
        raise
    finally:
        try:
            await client.close()
        except Exception:  # noqa: BLE001 - avoid masking upstream exceptions
            logger.exception("failed to close Codeforces client for handle=%s", handle)

    problem_examples: Dict[Tuple[int, str], Dict[str, Any]] = {}
    submissions_by_id: Dict[int, Dict[str, Any]] = {}

    for raw_submission, sid in fetched_new_submissions:
        problem = raw_submission.get("problem", {})
        contest_id = problem.get("contestId")
        index = problem.get("index")

        if contest_id is not None and index is not None:
            key = (int(contest_id), str(index))
            problem_examples[key] = problem

        author_handle = handle
        author = raw_submission.get("author")
        if isinstance(author, dict):
            members = author.get("members") or []
            if members and isinstance(members[0], dict) and members[0].get("handle"):
                author_handle = str(members[0]["handle"])

        submissions_by_id[sid] = {
            "id": sid,
            "user_id": int(user_id),
            "contest_id": int(raw_submission.get("contestId")) if raw_submission.get("contestId") is not None else None,
            "creation_time_seconds": int(raw_submission.get("creationTimeSeconds", 0)),
            "relative_time_seconds": (
                int(raw_submission.get("relativeTimeSeconds"))
                if raw_submission.get("relativeTimeSeconds") is not None
                else None
            ),
            "author_handle": author_handle,
            "problem_contest_id": int(contest_id) if contest_id is not None else None,
            "problem_index": str(index) if index is not None else None,
            "verdict": raw_submission.get("verdict"),
            "test_count": int(raw_submission.get("passedTestCount")) if raw_submission.get("passedTestCount") is not None else None,
            "time_consumed_ms": (
                int(raw_submission.get("timeConsumedMillis"))
                if raw_submission.get("timeConsumedMillis") is not None
                else None
            ),
        }

    problem_rows = [
        {
            "contest_id": contest_id,
            "index": index,
            "name": problem.get("name"),
            "rating": problem.get("rating"),
            "tags": problem.get("tags"),
        }
        for (contest_id, index), problem in problem_examples.items()
    ]
    submission_rows = list(submissions_by_id.values())

    inserted_count = 0
    async with db.begin():
        for i in range(0, len(problem_rows), batch_size):
            batch = problem_rows[i : i + batch_size]
            if not batch:
                continue
            await db.execute(
                pg_insert(Problem.__table__)
                .values(batch)
                .on_conflict_do_nothing(index_elements=["contest_id", "index"])
            )

        for i in range(0, len(submission_rows), batch_size):
            batch = submission_rows[i : i + batch_size]
            if not batch:
                continue
            inserted = await db.execute(
                pg_insert(Submission.__table__)
                .values(batch)
                .on_conflict_do_nothing(index_elements=["id"])
                .returning(Submission.id)
            )
            inserted_count += len(inserted.fetchall())

        if newest_seen_id is not None and (
            last_synced_submission_id is None or int(newest_seen_id) > int(last_synced_submission_id)
        ):
            await db.execute(
                sa_update(User)
                .where(User.id == int(user_id))
                .values(last_synced_submission_id=int(newest_seen_id))
            )

    logger.info("sync_user_submissions: %d new submissions added for %s", inserted_count, handle)
    return inserted_count
