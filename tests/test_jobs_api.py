from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.api.v1.endpoints import jobs as jobs_endpoint
from app.main import app


client = TestClient(app)


class FakeJobService:
    def list_jobs(self, db, limit: int, offset: int):
        return [
            SimpleNamespace(
                id=1,
                source_id=1,
                company_id=1,
                external_id="job-1",
                title="Python Backend Developer",
                description="Backend role",
                location="Yerevan",
                remote_type="hybrid",
                employment_type="full-time",
                apply_url="https://example.com/jobs/1",
                salary_min=None,
                salary_max=None,
                currency=None,
                published_at=None,
                source=SimpleNamespace(
                    id=1,
                    name="Example Source",
                    base_url="https://example.com",
                    is_active=True,
                ),
                company=SimpleNamespace(
                    id=1,
                    name="Example LLC",
                    normalized_name="example llc",
                    website_url="https://example.com",
                ),
            )
        ]

    def get_job_by_id(self, db, job_id: int):
        if job_id == 1:
            return self.list_jobs(db=db, limit=1, offset=0)[0]

        from fastapi import HTTPException, status

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )


def test_list_jobs_returns_jobs(monkeypatch) -> None:
    monkeypatch.setattr(jobs_endpoint, "job_service", FakeJobService())

    response = client.get("/jobs")

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": 1,
            "source_id": 1,
            "company_id": 1,
            "external_id": "job-1",
            "title": "Python Backend Developer",
            "description": "Backend role",
            "location": "Yerevan",
            "remote_type": "hybrid",
            "employment_type": "full-time",
            "apply_url": "https://example.com/jobs/1",
            "salary_min": None,
            "salary_max": None,
            "currency": None,
            "published_at": None,
            "source": {
                "id": 1,
                "name": "Example Source",
                "base_url": "https://example.com",
                "is_active": True,
            },
            "company": {
                "id": 1,
                "name": "Example LLC",
                "normalized_name": "example llc",
                "website_url": "https://example.com",
            },
        }
    ]


def test_get_job_returns_single_job(monkeypatch) -> None:
    monkeypatch.setattr(jobs_endpoint, "job_service", FakeJobService())

    response = client.get("/jobs/1")

    assert response.status_code == 200
    assert response.json()["id"] == 1
    assert response.json()["title"] == "Python Backend Developer"


def test_get_unknown_job_returns_404(monkeypatch) -> None:
    monkeypatch.setattr(jobs_endpoint, "job_service", FakeJobService())

    response = client.get("/jobs/999999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Job not found"}


def test_jobs_invalid_pagination_returns_422() -> None:
    response = client.get("/jobs?limit=0&offset=-1")

    assert response.status_code == 422
