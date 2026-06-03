from collections.abc import Iterator
from contextlib import contextmanager

import httpx

from app.integrations.job_sources.base import (
    JobSourceAdapter,
    JobSourceError,
)
from app.integrations.job_sources.remoteok import RemoteOKJobSourceAdapter
from app.models.job_source import JobSource


class UnsupportedJobSourceError(JobSourceError):
    """Raised when no adapter is registered for a job source."""


class JobSourceAdapterRegistry:
    @contextmanager
    def open_adapter(
        self,
        source: JobSource,
    ) -> Iterator[JobSourceAdapter]:
        normalized_name = source.name.strip().casefold().replace(" ", "")

        if normalized_name != "remoteok":
            raise UnsupportedJobSourceError(
                f"Unsupported job source: {source.name}"
            )

        base_url = source.base_url or "https://remoteok.com"

        with httpx.Client(
            base_url=base_url,
            timeout=5.0,
        ) as client:
            yield RemoteOKJobSourceAdapter(client)
