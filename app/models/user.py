from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # email must be unique and indexed, and cannot be null
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)

    # stored hashed password, not plain password
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    # optional Codeforces handle
    handle: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, unique=True)

    # track last synced submission id from Codeforces
    last_synced_submission_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # record creation timestamp with DB default
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self) -> str:  # pragma: no cover - trivial
        return f"<User id={self.id!r} email={self.email!r}>"
