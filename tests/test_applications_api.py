from datetime import datetime, timezone
from types import SimpleNamespace

from fastapi import HTTPException, status
from fastapi.testclient import TestClient

from app.api.dependencies import get_current_user
from app.api.v1.endpoints import applications as applications_endpoint
from app.main import app
from app.schemas.application import ApplicationStatus


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


def make_application(
    *,
    application_id: int,
    job_id: int,
    application_status: str,
    notes: str | None = None,
):
    now = datetime(2026, 6, 7, 12, 0, tzinfo=timezone.utc)

    return SimpleNamespace(
        id=application_id,
        job_id=job_id,
        status=application_status,
        notes=notes,
        applied_at=None,
        created_at=now,
        updated_at=now,
        job=make_job(job_id),
    )


class FakeApplicationService:
    def __init__(self) -> None:
        self.last_created_user_id: int | None = None
        self.last_created_job_id: int | None = None
        self.last_created_status: ApplicationStatus | None = None
        self.last_created_notes: str | None = None

        self.last_listed_user_id: int | None = None

        self.last_updated_application_id: int | None = None
        self.last_updated_user_id: int | None = None
        self.last_updated_status: ApplicationStatus | None = None

    def create_application(
        self,
        db,
        *,
        user_id: int,
        job_id: int,
        application_status: ApplicationStatus,
        notes: str | None,
    ):
        self.last_created_user_id = user_id
        self.last_created_job_id = job_id
        self.last_created_status = application_status
        self.last_created_notes = notes

        if job_id == 999999:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found",
            )

        if job_id == 409:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Application already exists",
            )

        return make_application(
            application_id=1,
            job_id=job_id,
            application_status=application_status.value,
            notes=notes,
        )

    def list_applications(
        self,
        db,
        *,
        user_id: int,
    ):
        self.last_listed_user_id = user_id

        return [
            make_application(
                application_id=user_id,
                job_id=100 + user_id,
                application_status="planned",
            )
        ]

    def update_application_status(
        self,
        db,
        *,
        application_id: int,
        user_id: int,
        new_status: ApplicationStatus,
    ):
        self.last_updated_application_id = application_id
        self.last_updated_user_id = user_id
        self.last_updated_status = new_status

        if application_id == 999999:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Application not found",
            )

        return make_application(
            application_id=application_id,
            job_id=12,
            application_status=new_status.value,
        )


def test_create_application_returns_created_application(monkeypatch) -> None:
    fake_service = FakeApplicationService()
    current_user = make_current_user(user_id=7)

    monkeypatch.setattr(
        applications_endpoint,
        "application_service",
        fake_service,
    )
    app.dependency_overrides[get_current_user] = lambda: current_user

    try:
        response = client.post(
            "/applications",
            json={
                "job_id": 12,
                "status": "planned",
                "notes": "Update CV first",
            },
        )
    finally:
        app.dependency_overrides.pop(get_current_user, None)

    assert response.status_code == 201
    assert response.json()["id"] == 1
    assert response.json()["job_id"] == 12
    assert response.json()["status"] == "planned"
    assert response.json()["notes"] == "Update CV first"
    assert response.json()["job"]["id"] == 12


def test_create_application_uses_authenticated_user_id(monkeypatch) -> None:
    fake_service = FakeApplicationService()
    current_user = make_current_user(user_id=7)

    monkeypatch.setattr(
        applications_endpoint,
        "application_service",
        fake_service,
    )
    app.dependency_overrides[get_current_user] = lambda: current_user

    try:
        response = client.post(
            "/applications",
            json={
                "job_id": 12,
                "status": "applied",
            },
        )
    finally:
        app.dependency_overrides.pop(get_current_user, None)

    assert response.status_code == 201
    assert fake_service.last_created_user_id == 7
    assert fake_service.last_created_job_id == 12
    assert fake_service.last_created_status == ApplicationStatus.APPLIED


def test_create_application_without_token_returns_401() -> None:
    response = client.post(
        "/applications",
        json={
            "job_id": 12,
            "status": "planned",
        },
    )

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Not authenticated",
    }


def test_create_application_for_unknown_job_returns_404(monkeypatch) -> None:
    fake_service = FakeApplicationService()
    current_user = make_current_user(user_id=7)

    monkeypatch.setattr(
        applications_endpoint,
        "application_service",
        fake_service,
    )
    app.dependency_overrides[get_current_user] = lambda: current_user

    try:
        response = client.post(
            "/applications",
            json={
                "job_id": 999999,
                "status": "planned",
            },
        )
    finally:
        app.dependency_overrides.pop(get_current_user, None)

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Job not found",
    }


def test_create_duplicate_application_returns_409(monkeypatch) -> None:
    fake_service = FakeApplicationService()
    current_user = make_current_user(user_id=7)

    monkeypatch.setattr(
        applications_endpoint,
        "application_service",
        fake_service,
    )
    app.dependency_overrides[get_current_user] = lambda: current_user

    try:
        response = client.post(
            "/applications",
            json={
                "job_id": 409,
                "status": "planned",
            },
        )
    finally:
        app.dependency_overrides.pop(get_current_user, None)

    assert response.status_code == 409
    assert response.json() == {
        "detail": "Application already exists",
    }


def test_create_application_rejects_unknown_status(monkeypatch) -> None:
    fake_service = FakeApplicationService()
    current_user = make_current_user(user_id=7)

    monkeypatch.setattr(
        applications_endpoint,
        "application_service",
        fake_service,
    )
    app.dependency_overrides[get_current_user] = lambda: current_user

    try:
        response = client.post(
            "/applications",
            json={
                "job_id": 12,
                "status": "intervew",
            },
        )
    finally:
        app.dependency_overrides.pop(get_current_user, None)

    assert response.status_code == 422


def test_list_applications_uses_authenticated_user_id(monkeypatch) -> None:
    fake_service = FakeApplicationService()
    current_user = make_current_user(user_id=9)

    monkeypatch.setattr(
        applications_endpoint,
        "application_service",
        fake_service,
    )
    app.dependency_overrides[get_current_user] = lambda: current_user

    try:
        response = client.get("/applications")
    finally:
        app.dependency_overrides.pop(get_current_user, None)

    assert response.status_code == 200
    assert fake_service.last_listed_user_id == 9
    assert len(response.json()) == 1
    assert response.json()[0]["id"] == 9
    assert response.json()[0]["job_id"] == 109


def test_list_applications_without_token_returns_401() -> None:
    response = client.get("/applications")

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Not authenticated",
    }


def test_update_application_uses_authenticated_user_id(monkeypatch) -> None:
    fake_service = FakeApplicationService()
    current_user = make_current_user(user_id=7)

    monkeypatch.setattr(
        applications_endpoint,
        "application_service",
        fake_service,
    )
    app.dependency_overrides[get_current_user] = lambda: current_user

    try:
        response = client.patch(
            "/applications/25",
            json={
                "status": "interview",
            },
        )
    finally:
        app.dependency_overrides.pop(get_current_user, None)

    assert response.status_code == 200
    assert response.json()["id"] == 25
    assert response.json()["status"] == "interview"

    assert fake_service.last_updated_application_id == 25
    assert fake_service.last_updated_user_id == 7
    assert fake_service.last_updated_status == ApplicationStatus.INTERVIEW


def test_update_unknown_application_returns_404(monkeypatch) -> None:
    fake_service = FakeApplicationService()
    current_user = make_current_user(user_id=7)

    monkeypatch.setattr(
        applications_endpoint,
        "application_service",
        fake_service,
    )
    app.dependency_overrides[get_current_user] = lambda: current_user

    try:
        response = client.patch(
            "/applications/999999",
            json={
                "status": "interview",
            },
        )
    finally:
        app.dependency_overrides.pop(get_current_user, None)

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Application not found",
    }


def test_update_application_rejects_unknown_status(monkeypatch) -> None:
    fake_service = FakeApplicationService()
    current_user = make_current_user(user_id=7)

    monkeypatch.setattr(
        applications_endpoint,
        "application_service",
        fake_service,
    )
    app.dependency_overrides[get_current_user] = lambda: current_user

    try:
        response = client.patch(
            "/applications/25",
            json={
                "status": "intervew",
            },
        )
    finally:
        app.dependency_overrides.pop(get_current_user, None)

    assert response.status_code == 422
