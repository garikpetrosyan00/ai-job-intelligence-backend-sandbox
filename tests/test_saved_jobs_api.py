from datetime import datetime, timezone
from types import SimpleNamespace

from fastapi import HTTPException, status
from fastapi.testclient import TestClient

from app.api.dependencies import get_current_user
from app.api.v1.endpoints import saved_jobs as saved_jobs_endpoint
from app.main import app


client = TestClient(app)


def make_current_user(user_id: int):
    return SimpleNamespace(
        id=user_id,
        email=f"user-{user_id}@example.com",
        full_name=f"User {user_id}",
        is_active=True,
    )


def make_job(job_id: int):
    return SimpleNamespace(
        id=job_id,
        source_id=1,
        company_id=None,
        external_id=f"job-{job_id}",
        title=f"Python Backend Developer {job_id}",
        description=None,
        location="Yerevan",
        remote_type=None,
        employment_type=None,
        apply_url=f"https://example.com/jobs/{job_id}",
        salary_min=None,
        salary_max=None,
        currency=None,
        published_at=None,
        source=None,
        company=None,
    )


def make_saved_job(
    *,
    saved_job_id: int,
    job_id: int,
):
    now = datetime(2026, 6, 7, 10, 0, tzinfo=timezone.utc)

    return SimpleNamespace(
        id=saved_job_id,
        job_id=job_id,
        notes=None,
        created_at=now,
        updated_at=now,
        job=make_job(job_id),
    )


class FakeSavedJobService:
    def __init__(self) -> None:
        self.last_saved_user_id: int | None = None
        self.last_saved_job_id: int | None = None
        self.last_listed_user_id: int | None = None

    def save_job(
        self,
        db,
        *,
        user_id: int,
        job_id: int,
    ):
        self.last_saved_user_id = user_id
        self.last_saved_job_id = job_id

        if job_id == 999999:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found",
            )

        return make_saved_job(
            saved_job_id=1,
            job_id=job_id,
        )

    def list_saved_jobs(
        self,
        db,
        *,
        user_id: int,
    ):
        self.last_listed_user_id = user_id

        return [
            make_saved_job(
                saved_job_id=user_id,
                job_id=100 + user_id,
            )
        ]


def test_save_job_returns_created_saved_job(monkeypatch) -> None:
    fake_service = FakeSavedJobService()
    current_user = make_current_user(user_id=7)

    monkeypatch.setattr(
        saved_jobs_endpoint,
        "saved_job_service",
        fake_service,
    )
    app.dependency_overrides[get_current_user] = lambda: current_user

    try:
        response = client.post("/jobs/12/save")
    finally:
        app.dependency_overrides.pop(get_current_user, None)

    assert response.status_code == 201
    assert response.json()["id"] == 1
    assert response.json()["job_id"] == 12
    assert response.json()["job"]["id"] == 12
    assert response.json()["job"]["title"] == "Python Backend Developer 12"


def test_save_job_uses_authenticated_user_id(monkeypatch) -> None:
    fake_service = FakeSavedJobService()
    current_user = make_current_user(user_id=7)

    monkeypatch.setattr(
        saved_jobs_endpoint,
        "saved_job_service",
        fake_service,
    )
    app.dependency_overrides[get_current_user] = lambda: current_user

    try:
        response = client.post("/jobs/12/save")
    finally:
        app.dependency_overrides.pop(get_current_user, None)

    assert response.status_code == 201
    assert fake_service.last_saved_user_id == 7
    assert fake_service.last_saved_job_id == 12


def test_save_job_without_token_returns_401() -> None:
    response = client.post("/jobs/12/save")

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Not authenticated",
    }


def test_save_unknown_job_returns_404(monkeypatch) -> None:
    fake_service = FakeSavedJobService()
    current_user = make_current_user(user_id=7)

    monkeypatch.setattr(
        saved_jobs_endpoint,
        "saved_job_service",
        fake_service,
    )
    app.dependency_overrides[get_current_user] = lambda: current_user

    try:
        response = client.post("/jobs/999999/save")
    finally:
        app.dependency_overrides.pop(get_current_user, None)

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Job not found",
    }


def test_list_saved_jobs_uses_authenticated_user_id(monkeypatch) -> None:
    fake_service = FakeSavedJobService()
    current_user = make_current_user(user_id=9)

    monkeypatch.setattr(
        saved_jobs_endpoint,
        "saved_job_service",
        fake_service,
    )
    app.dependency_overrides[get_current_user] = lambda: current_user

    try:
        response = client.get("/me/saved-jobs")
    finally:
        app.dependency_overrides.pop(get_current_user, None)

    assert response.status_code == 200
    assert fake_service.last_listed_user_id == 9
    assert len(response.json()) == 1
    assert response.json()[0]["id"] == 9
    assert response.json()[0]["job_id"] == 109


def test_list_saved_jobs_without_token_returns_401() -> None:
    response = client.get("/me/saved-jobs")

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Not authenticated",
    }
