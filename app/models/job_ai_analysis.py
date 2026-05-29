from sqlalchemy import ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class JobAIAnalysis(Base, TimestampMixin):
    __tablename__ = "job_ai_analyses"

    __table_args__ = (
        UniqueConstraint("job_id", name="uq_job_ai_analyses_job_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    job_id: Mapped[int] = mapped_column(
        ForeignKey("jobs.id"),
        nullable=False,
    )

    provider: Mapped[str] = mapped_column(String(100), nullable=False, default="mock")
    prompt_version: Mapped[str | None] = mapped_column(String(50), nullable=True)

    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    required_skills: Mapped[list | None] = mapped_column(JSON, nullable=True)
    nice_to_have_skills: Mapped[list | None] = mapped_column(JSON, nullable=True)

    seniority_level: Mapped[str | None] = mapped_column(String(100), nullable=True)
    match_score: Mapped[int | None] = mapped_column(Integer, nullable=True)

    reasoning: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_response: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    job = relationship("Job")
