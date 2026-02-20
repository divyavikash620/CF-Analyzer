import logging
from typing import List, Tuple

from sqlalchemy import select, tuple_, update as sa_update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.clients.codeforces import make_codeforces_client, CodeforcesAPIError
from app.models.problem import Problem
from app.models.submission import Submission
from app.models.user import User

logger = logging.getLogger("app.services.codeforces")


async def sync_user_submissions(handle: str, db: AsyncSession, batch_size: int = 200) -> int:
    """Fetch submissions for `handle` from Codeforces and persist new problems
    and submissions. Commits in batches. Returns number of new submissions added.

    Note: this function creates a short-lived Codeforces client internally.
    """
    async with make_codeforces_client() as client:
        # obtain last synced submission id for this user (if any)
        stmt = select(User.last_synced_submission_id).where(User.handle == handle)
        res = await db.execute(stmt)
        row = res.fetchone()
        last_synced_id = row[0] if row else None

        # request only new submissions by passing last_synced_id as `from_`
        from_param = int(last_synced_id) if last_synced_id is not None else 1
        try:
            raw = await client.get_user_submissions(handle, from_=from_param)
        except CodeforcesAPIError as exc:
            logger.error("failed to fetch submissions for %s: %s", handle, exc)
            raise

    # normalize raw -> list of submissions
    submissions = raw if isinstance(raw, list) else []
        if not submissions:
            return 0

    # collect problem keys and submission ids
    problem_keys: List[Tuple[int, str]] = []
    submission_ids: List[int] = []
    submission_rows = []
    problem_example: dict = {}

    for s in submissions:
        sid = s.get("id") or s.get("submissionId") or s.get("submissionId")
        if sid is None:
            continue
        submission_ids.append(int(sid))
        prob = s.get("problem", {})
        contest_id = prob.get("contestId")
        index = prob.get("index")
        if contest_id is not None and index is not None:
            problem_keys.append((int(contest_id), index))
            # keep a representative problem payload for enrichment
            problem_example[(int(contest_id), index)] = prob

        submission_rows.append((s, int(sid)))

    # deduplicate problem keys
    problem_keys = list(dict.fromkeys(problem_keys))

    # prepare problem rows (no pre-existence checks) and insert using
    # PostgreSQL ON CONFLICT DO NOTHING on the composite primary key
    problem_rows = []
    for (cid, idx) in problem_keys:
        rep = problem_example.get((cid, idx), {})
        name = rep.get("name")
        rating = rep.get("rating")
        tags = rep.get("tags")
        problem_rows.append({
            "contest_id": cid,
            "index": idx,
            "name": name,
            "rating": rating,
            "tags": tags,
        })

    if problem_rows:
        # insert in batches, committing once per batch
        for i in range(0, len(problem_rows), batch_size):
            batch = problem_rows[i : i + batch_size]
            stmt = (
                pg_insert(Problem.__table__)
                .values(batch)
                .on_conflict_do_nothing(index_elements=["contest_id", "index"])
            )
            async with db.begin():
                await db.execute(stmt)

    # prepare dict rows for bulk upsert (dedupe by id to avoid intra-batch conflicts)
    rows_by_id = {}
    for raw_s, sid in submission_rows:
        prob = raw_s.get("problem", {})
        contest_id = prob.get("contestId")
        index = prob.get("index")
        rows_by_id[sid] = {
            "id": int(sid),
            "contest_id": int(raw_s.get("contestId")) if raw_s.get("contestId") is not None else None,
            "creation_time_seconds": int(raw_s.get("creationTimeSeconds", 0)),
            "relative_time_seconds": raw_s.get("relativeTimeSeconds"),
            "author_handle": (raw_s.get("author", {}).get("members", [{}])[0].get("handle") if raw_s.get("author") else handle),
            "problem_contest_id": int(contest_id) if contest_id is not None else None,
            "problem_index": index,
            "verdict": raw_s.get("verdict"),
            "test_count": (int(raw_s.get("passedTestCount")) if raw_s.get("passedTestCount") is not None else None),
            "time_consumed_ms": (int(raw_s.get("timeConsumedMillis")) if raw_s.get("timeConsumedMillis") is not None else None),
        }

    to_insert_rows = list(rows_by_id.values())

    added = 0
    if to_insert_rows:
        # perform a single transactional bulk insert that ignores conflicts on primary key
        stmt = (
            pg_insert(Submission.__table__)
            .values(to_insert_rows)
            .on_conflict_do_nothing(index_elements=["id"])
            .returning(Submission.id)
        )
        async with db.begin():
            res = await db.execute(stmt)
            fetched = res.fetchall()
        added = len(fetched)

        # update user's last_synced_submission_id to the max id we just fetched
        try:
            max_id = max(int(r.get("id")) for r in submissions if (r.get("id") or r.get("submissionId")))
        except ValueError:
            max_id = None

        if max_id is not None:
            async with db.begin():
                await db.execute(
                    sa_update(User).where(User.handle == handle).values(last_synced_submission_id=max_id)
                )

        logger.info("sync_user_submissions: %d new submissions added for %s", added, handle)
        return added
