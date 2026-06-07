from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict

from app.schemas.job import JobRead


class ApplicationStatus(str, Enum):
    PLANNED = "planned"
    APPLIED = "applied"
    INTERVIEW = "interview"
    OFFER = "offer"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


class ApplicationCreate(BaseModel):
    job_id: int
    status: ApplicationStatus = ApplicationStatus.PLANNED
    notes: str | None = None


class ApplicationUpdate(BaseModel):
    status: ApplicationStatus


class ApplicationRead(BaseModel):
    id: int
    job_id: int
    status: ApplicationStatus
    notes: str | None = None
    applied_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    job: JobRead

    model_config = ConfigDict(from_attributes=True)
