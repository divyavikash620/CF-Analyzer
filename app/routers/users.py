from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash
from app.db.session import get_async_session
from app.models.user import User
from app.schemas.user import UserCreate, UserOut

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def create_user(user_in: UserCreate, db: AsyncSession = Depends(get_async_session)) -> User:
    """Create a new user: hash password, save, handle duplicate email."""
    hashed = get_password_hash(user_in.password)
    user = User(email=user_in.email, hashed_password=hashed)
    db.add(user)
    try:
        await db.commit()
        await db.refresh(user)
        return user
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
