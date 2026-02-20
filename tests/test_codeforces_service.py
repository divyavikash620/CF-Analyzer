"""Tests for sync_user_submissions service.

To run these tests, ensure the following dev dependencies are installed:
  - pytest-asyncio
  - aiosqlite

Run with: pytest tests/test_codeforces_service.py
"""
import pytest
from unittest.mock import AsyncMock, patch
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.models.user import User
from app.models.problem import Problem
from app.models.submission import Submission
from app.db.base import Base
from app.services.codeforces_service import sync_user_submissions


@pytest.fixture
async def async_db():
    """Create an in-memory async SQLite database for testing."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=StaticPool,
        echo=False,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session_maker() as session:
        yield session

    await engine.dispose()


@pytest.fixture
async def test_user(async_db: AsyncSession):
    """Create a test user with a handle."""
    user = User(
        email="test@example.com",
        hashed_password="hashed_pass",
        handle="test_handle",
    )
    async_db.add(user)
    await async_db.commit()
    await async_db.refresh(user)
    return user


@pytest.mark.asyncio
async def test_sync_no_submissions(async_db: AsyncSession, test_user: User):
    """Test sync when Codeforces returns no submissions."""
    mock_client = AsyncMock()
    mock_client.get_user_submissions = AsyncMock(return_value=[])

    with patch("app.services.codeforces_service.make_codeforces_client") as mock_make_client:
        mock_make_client.return_value.__aenter__.return_value = mock_client

        result = await sync_user_submissions(test_user.handle, async_db)

    assert result == 0

    # Verify no submissions were inserted
    q = await async_db.execute(select(Submission))
    submissions = q.scalars().all()
    assert len(submissions) == 0

    # Verify last_synced_submission_id was not updated
    q = await async_db.execute(select(User).where(User.id == test_user.id))
    user = q.scalar_one()
    assert user.last_synced_submission_id is None


@pytest.mark.asyncio
async def test_sync_new_submissions_inserted(async_db: AsyncSession, test_user: User):
    """Test that new submissions are correctly inserted."""
    mock_submissions = [
        {
            "id": 100,
            "contestId": 1000,
            "creationTimeSeconds": 1234567890,
            "relativeTimeSeconds": 100,
            "author": {"members": [{"handle": "test_handle"}]},
            "problem": {
                "contestId": 1000,
                "index": "A",
                "name": "Problem A",
                "rating": 800,
                "tags": ["implementation"],
            },
            "verdict": "OK",
            "passedTestCount": 5,
            "timeConsumedMillis": 500,
        },
        {
            "id": 101,
            "contestId": 1000,
            "creationTimeSeconds": 1234567891,
            "relativeTimeSeconds": 200,
            "author": {"members": [{"handle": "test_handle"}]},
            "problem": {
                "contestId": 1000,
                "index": "B",
                "name": "Problem B",
                "rating": 1000,
                "tags": ["dp"],
            },
            "verdict": "WRONG_ANSWER",
            "passedTestCount": 2,
            "timeConsumedMillis": 1000,
        },
    ]

    mock_client = AsyncMock()
    mock_client.get_user_submissions = AsyncMock(return_value=mock_submissions)

    with patch("app.services.codeforces_service.make_codeforces_client") as mock_make_client:
        mock_make_client.return_value.__aenter__.return_value = mock_client

        result = await sync_user_submissions(test_user.handle, async_db)

    assert result == 2

    # Verify both submissions were inserted
    q = await async_db.execute(select(Submission).order_by(Submission.id))
    submissions = q.scalars().all()
    assert len(submissions) == 2
    assert submissions[0].id == 100
    assert submissions[0].verdict == "OK"
    assert submissions[1].id == 101
    assert submissions[1].verdict == "WRONG_ANSWER"

    # Verify problems were inserted
    q = await async_db.execute(select(Problem).order_by(Problem.contest_id, Problem.index))
    problems = q.scalars().all()
    assert len(problems) == 2
    assert problems[0].contest_id == 1000
    assert problems[0].index == "A"
    assert problems[0].rating == 800
    assert problems[1].index == "B"
    assert problems[1].rating == 1000

    # Verify last_synced_submission_id was updated to max submission id
    q = await async_db.execute(select(User).where(User.id == test_user.id))
    user = q.scalar_one()
    assert user.last_synced_submission_id == 101


@pytest.mark.asyncio
async def test_sync_partial_duplicates(async_db: AsyncSession, test_user: User):
    """Test sync with partial duplicates (some submissions already exist)."""
    # First, insert one existing submission
    existing_problem = Problem(
        contest_id=1000,
        index="A",
        name="Problem A",
        rating=800,
        tags=["implementation"],
    )
    async_db.add(existing_problem)
    await async_db.commit()

    existing_submission = Submission(
        id=100,
        contest_id=1000,
        creation_time_seconds=1234567890,
        relative_time_seconds=100,
        author_handle="test_handle",
        problem_contest_id=1000,
        problem_index="A",
        verdict="OK",
        test_count=5,
        time_consumed_ms=500,
    )
    async_db.add(existing_submission)
    await async_db.commit()

    # Now sync with one existing and one new submission
    mock_submissions = [
        {
            "id": 100,  # duplicate
            "contestId": 1000,
            "creationTimeSeconds": 1234567890,
            "relativeTimeSeconds": 100,
            "author": {"members": [{"handle": "test_handle"}]},
            "problem": {
                "contestId": 1000,
                "index": "A",
                "name": "Problem A",
                "rating": 800,
                "tags": ["implementation"],
            },
            "verdict": "OK",
            "passedTestCount": 5,
            "timeConsumedMillis": 500,
        },
        {
            "id": 102,  # new
            "contestId": 1001,
            "creationTimeSeconds": 1234567892,
            "relativeTimeSeconds": 300,
            "author": {"members": [{"handle": "test_handle"}]},
            "problem": {
                "contestId": 1001,
                "index": "C",
                "name": "Problem C",
                "rating": 1200,
                "tags": ["graph"],
            },
            "verdict": "ACCEPTED",
            "passedTestCount": 10,
            "timeConsumedMillis": 2000,
        },
    ]

    mock_client = AsyncMock()
    mock_client.get_user_submissions = AsyncMock(return_value=mock_submissions)

    with patch("app.services.codeforces_service.make_codeforces_client") as mock_make_client:
        mock_make_client.return_value.__aenter__.return_value = mock_client

        result = await sync_user_submissions(test_user.handle, async_db)

    # Only the new submission should be counted
    assert result == 1

    # Verify total submissions in DB
    q = await async_db.execute(select(Submission).order_by(Submission.id))
    submissions = q.scalars().all()
    assert len(submissions) == 2
    assert submissions[0].id == 100
    assert submissions[1].id == 102

    # Verify last_synced_submission_id was updated
    q = await async_db.execute(select(User).where(User.id == test_user.id))
    user = q.scalar_one()
    assert user.last_synced_submission_id == 102


@pytest.mark.asyncio
async def test_sync_updates_last_synced_id(async_db: AsyncSession, test_user: User):
    """Test that last_synced_submission_id is updated to the maximum submission id."""
    test_user.last_synced_submission_id = 50
    await async_db.commit()

    mock_submissions = [
        {
            "id": 51,
            "contestId": 1000,
            "creationTimeSeconds": 1234567890,
            "relativeTimeSeconds": 100,
            "author": {"members": [{"handle": "test_handle"}]},
            "problem": {
                "contestId": 1000,
                "index": "A",
                "name": "Problem A",
                "rating": 800,
                "tags": ["implementation"],
            },
            "verdict": "OK",
            "passedTestCount": 5,
            "timeConsumedMillis": 500,
        },
        {
            "id": 60,  # higher id
            "contestId": 1001,
            "creationTimeSeconds": 1234567891,
            "relativeTimeSeconds": 200,
            "author": {"members": [{"handle": "test_handle"}]},
            "problem": {
                "contestId": 1001,
                "index": "B",
                "name": "Problem B",
                "rating": 1000,
                "tags": ["dp"],
            },
            "verdict": "WRONG_ANSWER",
            "passedTestCount": 2,
            "timeConsumedMillis": 1000,
        },
    ]

    mock_client = AsyncMock()
    mock_client.get_user_submissions = AsyncMock(return_value=mock_submissions)

    with patch("app.services.codeforces_service.make_codeforces_client") as mock_make_client:
        mock_make_client.return_value.__aenter__.return_value = mock_client

        result = await sync_user_submissions(test_user.handle, async_db)

    assert result == 2

    # Verify last_synced_submission_id is updated to the maximum id (60, not 51)
    q = await async_db.execute(select(User).where(User.id == test_user.id))
    user = q.scalar_one()
    assert user.last_synced_submission_id == 60


@pytest.mark.asyncio
async def test_sync_with_missing_fields(async_db: AsyncSession, test_user: User):
    """Test sync handles submissions with missing optional fields gracefully."""
    mock_submissions = [
        {
            "id": 200,
            "contestId": 2000,
            "creationTimeSeconds": 1234567900,
            # missing relativeTimeSeconds
            "author": {"members": [{"handle": "test_handle"}]},
            "problem": {
                "contestId": 2000,
                "index": "X",
                "name": "Problem X",
                # missing rating
                # missing tags
            },
            "verdict": "RUNTIME_ERROR",
            # missing passedTestCount
            # missing timeConsumedMillis
        },
    ]

    mock_client = AsyncMock()
    mock_client.get_user_submissions = AsyncMock(return_value=mock_submissions)

    with patch("app.services.codeforces_service.make_codeforces_client") as mock_make_client:
        mock_make_client.return_value.__aenter__.return_value = mock_client

        result = await sync_user_submissions(test_user.handle, async_db)

    assert result == 1

    # Verify submission was inserted with None values for optional fields
    q = await async_db.execute(select(Submission).where(Submission.id == 200))
    submission = q.scalar_one()
    assert submission.verdict == "RUNTIME_ERROR"
    assert submission.relative_time_seconds is None
    assert submission.test_count is None
    assert submission.time_consumed_ms is None

    # Verify problem was inserted with None for optional fields
    q = await async_db.execute(select(Problem).where(Problem.contest_id == 2000))
    problem = q.scalar_one()
    assert problem.rating is None
    assert problem.tags is None
