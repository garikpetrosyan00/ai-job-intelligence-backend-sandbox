from pydantic import BaseModel, ConfigDict


class CompanyRead(BaseModel):
    id: int
    name: str
    normalized_name: str
    website_url: str | None = None

    model_config = ConfigDict(from_attributes=True)
