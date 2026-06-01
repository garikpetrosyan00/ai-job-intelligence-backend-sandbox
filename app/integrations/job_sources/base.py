from datetime import datetime
from typing import Any, Protocol

from pydantic import BaseModel, Field


class ExternalJobDTO(BaseModel):
    external_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    company_name: str | None = None
    location: str | None = None
    description: str | None = None
    apply_url: str | None = None
    published_at: datetime | None = None
    raw_payload: dict[str, Any] = Field(default_factory=dict)


class JobSourceAdapter(Protocol):
    def fetch_jobs(self, limit: int) -> list[ExternalJobDTO]:
        ...


class JobSourceError(Exception):
    """Base error for external job source integrations."""


class JobSourceTimeoutError(JobSourceError):
    """Raised when an external job source does not respond in time."""


class JobSourceResponseError(JobSourceError):
    """Raised when an external job source returns an invalid response."""
