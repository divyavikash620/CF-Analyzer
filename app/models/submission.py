from typing import Optional

from sqlalchemy import ForeignKey, ForeignKeyConstraint, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Submission(Base):
    __tablename__ = "submissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    contest_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    creation_time_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    relative_time_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    author_handle: Mapped[str] = mapped_column(String(100), nullable=False)
    problem_contest_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    problem_index: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    verdict: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    test_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    time_consumed_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    __table_args__ = (
        ForeignKeyConstraint(
            ["problem_contest_id", "problem_index"],
            ["problems.contest_id", "problems.index"],
            ondelete="SET NULL",
        ),
        Index("idx_submissions_user_id", "user_id"),
        Index("idx_submissions_author_handle", "author_handle"),
        Index("idx_submissions_problem", "problem_contest_id", "problem_index"),
    )

    def __repr__(self) -> str:  # pragma: no cover - trivial
        return f"<Submission id={self.id} handle={self.author_handle} problem={self.problem_contest_id}{self.problem_index}>"
