from typing import Any

import httpx
from pydantic import ValidationError

from app.integrations.job_sources.base import (
    ExternalJobDTO,
    JobSourceResponseError,
    JobSourceTimeoutError,
)


class RemoteOKJobSourceAdapter:
    def __init__(self, client: httpx.Client) -> None:
        self.client = client

    def fetch_jobs(self, limit: int) -> list[ExternalJobDTO]:
        if limit < 1:
            raise ValueError("limit must be greater than 0")

        try:
            response = self.client.get("/api")
            response.raise_for_status()
            payload = response.json()

        except httpx.TimeoutException as exc:
            raise JobSourceTimeoutError(
                "Remote OK API request timed out"
            ) from exc

        except httpx.HTTPStatusError as exc:
            raise JobSourceResponseError(
                f"Remote OK API returned HTTP {exc.response.status_code}"
            ) from exc

        except httpx.RequestError as exc:
            raise JobSourceResponseError(
                "Could not connect to Remote OK API"
            ) from exc

        except ValueError as exc:
            raise JobSourceResponseError(
                "Remote OK API returned invalid JSON"
            ) from exc

        if not isinstance(payload, list):
            raise JobSourceResponseError(
                "Remote OK API payload must be a list"
            )

        jobs: list[ExternalJobDTO] = []

        for item in payload:
            if self._is_metadata_item(item):
                continue

            jobs.append(self._map_job(item))

            if len(jobs) >= limit:
                break

        return jobs

    @staticmethod
    def _is_metadata_item(item: Any) -> bool:
        return (
            isinstance(item, dict)
            and "legal" in item
            and "id" not in item
        )

    @staticmethod
    def _map_job(item: Any) -> ExternalJobDTO:
        if not isinstance(item, dict):
            raise JobSourceResponseError(
                "Remote OK job item must be an object"
            )

        try:
            return ExternalJobDTO(
                external_id=RemoteOKJobSourceAdapter._required_id(
                    item.get("id")
                ),
                title=RemoteOKJobSourceAdapter._required_text(
                    item.get("position"),
                    field_name="position",
                ),
                company_name=RemoteOKJobSourceAdapter._optional_text(
                    item.get("company")
                ),
                location=RemoteOKJobSourceAdapter._optional_text(
                    item.get("location")
                ),
                description=RemoteOKJobSourceAdapter._optional_text(
                    item.get("description")
                ),
                apply_url=RemoteOKJobSourceAdapter._optional_text(
                    item.get("apply_url") or item.get("url")
                ),
                published_at=item.get("date"),
                raw_payload=item,
            )

        except ValidationError as exc:
            raise JobSourceResponseError(
                "Remote OK API returned invalid job data"
            ) from exc

    @staticmethod
    def _required_id(value: Any) -> str:
        if value is None:
            raise JobSourceResponseError(
                "Remote OK job id is required"
            )

        cleaned = str(value).strip()

        if not cleaned:
            raise JobSourceResponseError(
                "Remote OK job id cannot be empty"
            )

        return cleaned

    @staticmethod
    def _required_text(
        value: Any,
        *,
        field_name: str,
    ) -> str:
        if not isinstance(value, str):
            raise JobSourceResponseError(
                f"Remote OK job {field_name} must be a string"
            )

        cleaned = value.strip()

        if not cleaned:
            raise JobSourceResponseError(
                f"Remote OK job {field_name} cannot be empty"
            )

        return cleaned

    @staticmethod
    def _optional_text(value: Any) -> str | None:
        if not isinstance(value, str):
            return None

        cleaned = value.strip()

        return cleaned or None
