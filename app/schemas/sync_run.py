from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SyncRunRead(BaseModel):
    id: int
    source_id: int

    status: str

    started_at: datetime
    finished_at: datetime | None = None

    jobs_fetched: int
    jobs_created: int
    jobs_updated: int

    error_message: str | None = None

    model_config = ConfigDict(from_attributes=True)
