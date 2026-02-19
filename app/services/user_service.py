from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.core.security import get_password_hash
from app.models.user import User
from app.services.codeforces_service import sync_user_submissions


async def create_user(db: AsyncSession, email: str, password: str) -> User:
    """Create a new user record.

    This hashes the password, attempts to insert the user, and commits the
    transaction. On unique constraint violations an IntegrityError is raised
    so the caller (router) can translate that into an HTTP response.
    """
    hashed = get_password_hash(password)
    user = User(email=email, hashed_password=hashed)
    db.add(user)
    try:
        await db.commit()
        await db.refresh(user)
        return user
    except IntegrityError:
        await db.rollback()
        raise


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    q = await db.execute(
        "SELECT * FROM users WHERE email = :email",
        {"email": email},
    )
    # prefer ORM query in callers; this helper kept minimal for convenience
    row = q.first()
    return row[0] if row is not None else None
