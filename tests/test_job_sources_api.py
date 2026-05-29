from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.api.v1.endpoints import job_sources as job_sources_endpoint
from app.main import app


client = TestClient(app)


class FakeJobSourceService:
    def list_sources(self, db, limit: int, offset: int):
        return [
            SimpleNamespace(
                id=1,
                name="Example Source",
                base_url="https://example.com",
                is_active=True,
            )
        ]


def test_list_job_sources_returns_sources(monkeypatch) -> None:
    monkeypatch.setattr(
        job_sources_endpoint,
        "job_source_service",
        FakeJobSourceService(),
    )

    response = client.get("/job-sources")

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": 1,
            "name": "Example Source",
            "base_url": "https://example.com",
            "is_active": True,
        }
    ]


def test_job_sources_invalid_pagination_returns_422() -> None:
    response = client.get("/job-sources?limit=0&offset=-1")

    assert response.status_code == 422
