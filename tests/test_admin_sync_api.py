from datetime import datetime, timezone
from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.api.v1.endpoints import admin_sync as admin_sync_endpoint
from app.main import app
from app.services.admin_sync import (
    JobSourceNotFoundError,
    JobSourceSyncError,
)


client = TestClient(app)


def create_sync_run(
    *,
    sync_run_id: int,
    status: str,
    jobs_fetched: int,
    jobs_created: int,
    jobs_updated: int,
    error_message: str | None,
):
    return SimpleNamespace(
        id=sync_run_id,
        source_id=1,
        status=status,
        started_at=datetime(
            2026,
            6,
            3,
            10,
            0,
            tzinfo=timezone.utc,
        ),
        finished_at=datetime(
            2026,
            6,
            3,
            10,
            0,
            2,
            tzinfo=timezone.utc,
        ),
        jobs_fetched=jobs_fetched,
        jobs_created=jobs_created,
        jobs_updated=jobs_updated,
        error_message=error_message,
    )


class FakeAdminSyncService:
    def __init__(self) -> None:
        self.received_list_args: list[tuple[int, int]] = []
        self.received_sync_args: list[tuple[int, int]] = []

    def list_runs(self, db, limit: int, offset: int):
        self.received_list_args.append((limit, offset))

        return [
            create_sync_run(
                sync_run_id=2,
                status="failed",
                jobs_fetched=0,
                jobs_created=0,
                jobs_updated=0,
                error_message="Remote OK API request timed out",
            ),
            create_sync_run(
                sync_run_id=1,
                status="succeeded",
                jobs_fetched=10,
                jobs_created=3,
                jobs_updated=1,
                error_message=None,
            ),
        ]

    def sync_source(self, db, source_id: int, limit: int):
        self.received_sync_args.append((source_id, limit))

        if source_id == 999999:
            raise JobSourceNotFoundError(
                "Job source was not found"
            )

        if source_id == 2:
            raise JobSourceSyncError(
                "Job source sync failed"
            )

        return create_sync_run(
            sync_run_id=3,
            status="succeeded",
            jobs_fetched=10,
            jobs_created=3,
            jobs_updated=1,
            error_message=None,
        )


def test_list_sync_runs_returns_history(monkeypatch) -> None:
    fake_service = FakeAdminSyncService()

    monkeypatch.setattr(
        admin_sync_endpoint,
        "admin_sync_service",
        fake_service,
    )

    response = client.get("/admin/sync-runs?limit=5&offset=2")

    assert response.status_code == 200

    payload = response.json()

    assert fake_service.received_list_args == [(5, 2)]

    assert len(payload) == 2

    assert payload[0]["id"] == 2
    assert payload[0]["status"] == "failed"
    assert payload[0]["jobs_fetched"] == 0
    assert payload[0]["error_message"] == "Remote OK API request timed out"

    assert payload[1]["id"] == 1
    assert payload[1]["status"] == "succeeded"
    assert payload[1]["jobs_fetched"] == 10
    assert payload[1]["jobs_created"] == 3
    assert payload[1]["jobs_updated"] == 1
    assert payload[1]["error_message"] is None


def test_list_sync_runs_invalid_pagination_returns_422() -> None:
    response = client.get("/admin/sync-runs?limit=0&offset=-1")

    assert response.status_code == 422


def test_sync_source_returns_successful_run(monkeypatch) -> None:
    fake_service = FakeAdminSyncService()

    monkeypatch.setattr(
        admin_sync_endpoint,
        "admin_sync_service",
        fake_service,
    )

    response = client.post("/admin/sources/1/sync?limit=5")

    assert response.status_code == 200
    assert fake_service.received_sync_args == [(1, 5)]

    payload = response.json()

    assert payload["id"] == 3
    assert payload["source_id"] == 1
    assert payload["status"] == "succeeded"
    assert payload["jobs_fetched"] == 10
    assert payload["jobs_created"] == 3
    assert payload["jobs_updated"] == 1
    assert payload["error_message"] is None


def test_sync_unknown_source_returns_404(monkeypatch) -> None:
    monkeypatch.setattr(
        admin_sync_endpoint,
        "admin_sync_service",
        FakeAdminSyncService(),
    )

    response = client.post("/admin/sources/999999/sync")

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Job source not found",
    }


def test_sync_failure_returns_502(monkeypatch) -> None:
    monkeypatch.setattr(
        admin_sync_endpoint,
        "admin_sync_service",
        FakeAdminSyncService(),
    )

    response = client.post("/admin/sources/2/sync")

    assert response.status_code == 502
    assert response.json() == {
        "detail": "Job source sync failed",
    }


def test_sync_invalid_limit_returns_422() -> None:
    response = client.post("/admin/sources/1/sync?limit=0")

    assert response.status_code == 422
