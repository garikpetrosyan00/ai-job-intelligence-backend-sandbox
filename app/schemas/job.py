from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from app.schemas.company import CompanyRead
from app.schemas.job_source import JobSourceRead


class JobRead(BaseModel):
    id: int

    source_id: int
    company_id: int | None = None

    external_id: str
    title: str
    description: str | None = None

    location: str | None = None
    remote_type: str | None = None
    employment_type: str | None = None

    apply_url: str | None = None

    salary_min: Decimal | None = None
    salary_max: Decimal | None = None
    currency: str | None = None

    published_at: datetime | None = None

    source: JobSourceRead | None = None
    company: CompanyRead | None = None

    model_config = ConfigDict(from_attributes=True)
