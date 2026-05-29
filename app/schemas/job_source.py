from pydantic import BaseModel, ConfigDict


class JobSourceRead(BaseModel):
    id: int
    name: str
    base_url: str | None = None
    is_active: bool

    model_config = ConfigDict(from_attributes=True)
