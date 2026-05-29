from sqlalchemy.orm import Session

from app.models.job_source import JobSource
from app.repositories.job_source import JobSourceRepository


class JobSourceService:
    def __init__(self, repository: JobSourceRepository | None = None) -> None:
        self.repository = repository or JobSourceRepository()

    def list_sources(self, db: Session, limit: int, offset: int) -> list[JobSource]:
        return self.repository.list_sources(db=db, limit=limit, offset=offset)
