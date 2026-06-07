from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.job import JobRead


class SavedJobRead(BaseModel):
    id: int
    job_id: int
    notes: str | None = None
    created_at: datetime
    updated_at: datetime

    job: JobRead

    model_config = ConfigDict(from_attributes=True)
