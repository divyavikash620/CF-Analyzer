import logging
from typing import List, Tuple

from sqlalchemy import select, tuple_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.clients.codeforces import make_codeforces_client, CodeforcesAPIError
from app.models.problem import Problem
from app.models.submission import Submission

logger = logging.getLogger("app.services.codeforces")


async def sync_user_submissions(handle: str, db: AsyncSession, batch_size: int = 200) -> int:
    """Fetch submissions for `handle` from Codeforces and persist new problems
    and submissions. Commits in batches. Returns number of new submissions added.

    Note: this function creates a short-lived Codeforces client internally.
    """
    client = make_codeforces_client()
    try:
        raw = await client.get_user_submissions(handle)
    except CodeforcesAPIError as exc:
        logger.error("failed to fetch submissions for %s: %s", handle, exc)
        await client._client.aclose()
        raise

    # normalize raw -> list of submissions
    submissions = raw if isinstance(raw, list) else []
    if not submissions:
        await client._client.aclose()
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

    # fetch existing problems
    existing_problems = set()
    if problem_keys:
        stmt = select(Problem.contest_id, Problem.index).where(
            tuple_(Problem.contest_id, Problem.index).in_(problem_keys)
        )
        res = await db.execute(stmt)
        existing_problems = set(res.fetchall())

    # insert missing problems (enrich with name, rating, tags if available)
    missing_problems = []
    for (cid, idx) in problem_keys:
        if (cid, idx) not in existing_problems:
            rep = problem_example.get((cid, idx), {})
            name = rep.get("name")
            rating = rep.get("rating")
            tags = rep.get("tags")
            missing_problems.append(Problem(contest_id=cid, index=idx, name=name, rating=rating, tags=tags))

    if missing_problems:
        db.add_all(missing_problems)
        try:
            await db.commit()
        except IntegrityError:
            await db.rollback()
            logger.info("some problems insertion conflicted, continuing")

    # fetch existing submission ids
    existing_sub_ids = set()
    if submission_ids:
        stmt = select(Submission.id).where(Submission.id.in_(submission_ids))
        res = await db.execute(stmt)
        existing_sub_ids = {row[0] for row in res.fetchall()}

    # prepare Submission objects for missing ones
    to_insert: List[Submission] = []
    for raw_s, sid in submission_rows:
        if sid in existing_sub_ids:
            continue
        prob = raw_s.get("problem", {})
        contest_id = prob.get("contestId")
        index = prob.get("index")
        sub = Submission(
            id=int(sid),
            contest_id=int(raw_s.get("contestId")) if raw_s.get("contestId") is not None else None,
            creation_time_seconds=int(raw_s.get("creationTimeSeconds", 0)),
            relative_time_seconds=raw_s.get("relativeTimeSeconds"),
            author_handle=(raw_s.get("author", {}).get("members", [{}])[0].get("handle") if raw_s.get("author") else handle),
            problem_contest_id=int(contest_id) if contest_id is not None else None,
            problem_index=index,
            verdict=raw_s.get("verdict"),
            test_count=(int(raw_s.get("passedTestCount")) if raw_s.get("passedTestCount") is not None else None),
            time_consumed_ms=(int(raw_s.get("timeConsumedMillis")) if raw_s.get("timeConsumedMillis") is not None else None),
        )
        to_insert.append(sub)

    # insert in batches
    added = 0
    for i in range(0, len(to_insert), batch_size):
        batch = to_insert[i : i + batch_size]
        db.add_all(batch)
        try:
            await db.commit()
            added += len(batch)
        except IntegrityError:
            await db.rollback()
            # some rows may conflict; try inserting one-by-one as fallback
            for row in batch:
                try:
                    db.add(row)
                    await db.commit()
                    added += 1
                except IntegrityError:
                    await db.rollback()
                    continue

    logger.info("sync_user_submissions: %d new submissions added for %s", added, handle)
    await client._client.aclose()
    return added
