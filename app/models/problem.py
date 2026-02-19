from typing import Optional

from sqlalchemy import Integer, String, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Problem(Base):
    __tablename__ = "problems"

    contest_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    index: Mapped[str] = mapped_column(String(20), primary_key=True)
    name: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    rating: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    tags: Mapped[Optional[object]] = mapped_column(JSON, nullable=True)

    def __repr__(self) -> str:  # pragma: no cover - trivial
        return f"<Problem {self.contest_id}{self.index} {self.name!r}>"
