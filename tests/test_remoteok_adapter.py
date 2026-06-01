import httpx
import pytest

from app.integrations.job_sources.base import (
    JobSourceResponseError,
)
from app.integrations.job_sources.remoteok import (
    RemoteOKJobSourceAdapter,
)


def test_fetch_jobs_maps_remoteok_payload_to_dto() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == "/api"

        return httpx.Response(
            status_code=200,
            json=[
                {
                    "legal": "API terms metadata",
                    "last_updated": 1710000000,
                },
                {
                    "id": "remote-job-1",
                    "date": "2026-06-01T10:30:00Z",
                    "company": "  Example Tech  ",
                    "position": "  Python Backend Developer  ",
                    "description": "  Build FastAPI services.  ",
                    "location": "  Remote  ",
                    "apply_url": "  https://example.com/jobs/remote-job-1  ",
                },
                {
                    "id": "remote-job-2",
                    "date": "2026-06-01T11:00:00Z",
                    "company": "Another Company",
                    "position": "Backend Engineer",
                    "description": "Work with PostgreSQL.",
                    "location": "Yerevan",
                    "apply_url": "https://example.com/jobs/remote-job-2",
                },
            ],
        )

    transport = httpx.MockTransport(handler)

    with httpx.Client(
        base_url="https://remoteok.test",
        transport=transport,
        timeout=5.0,
    ) as client:
        adapter = RemoteOKJobSourceAdapter(client=client)

        jobs = adapter.fetch_jobs(limit=1)

    assert len(jobs) == 1

    job = jobs[0]

    assert job.external_id == "remote-job-1"
    assert job.title == "Python Backend Developer"
    assert job.company_name == "Example Tech"
    assert job.location == "Remote"
    assert job.description == "Build FastAPI services."
    assert job.apply_url == "https://example.com/jobs/remote-job-1"
    assert job.published_at is not None
    assert job.raw_payload["position"] == "  Python Backend Developer  "


def test_fetch_jobs_rejects_job_without_position() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            status_code=200,
            json=[
                {
                    "legal": "API terms metadata",
                },
                {
                    "id": "remote-job-1",
                    "company": "Example Tech",
                    "location": "Remote",
                },
            ],
        )

    transport = httpx.MockTransport(handler)

    with httpx.Client(
        base_url="https://remoteok.test",
        transport=transport,
        timeout=5.0,
    ) as client:
        adapter = RemoteOKJobSourceAdapter(client=client)

        with pytest.raises(
            JobSourceResponseError,
            match="position must be a string",
        ):
            adapter.fetch_jobs(limit=1)
