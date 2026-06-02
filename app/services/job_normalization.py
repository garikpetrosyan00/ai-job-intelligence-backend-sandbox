from dataclasses import dataclass
from datetime import datetime
from typing import Any
from urllib.parse import urlsplit, urlunsplit

from app.integrations.job_sources.base import ExternalJobDTO


@dataclass(frozen=True)
class NormalizedExternalJobDTO:
    external_id: str
    title: str
    company_name: str | None
    company_normalized_name: str | None
    location: str | None
    description: str | None
    apply_url: str | None
    published_at: datetime | None
    raw_payload: dict[str, Any]


def normalize_external_job(job: ExternalJobDTO) -> NormalizedExternalJobDTO:
    external_id = _normalize_required_text(
        job.external_id,
        field_name="external_id",
    )
    title = _normalize_required_text(
        job.title,
        field_name="title",
    )
    company_name = _normalize_optional_text(job.company_name)

    return NormalizedExternalJobDTO(
        external_id=external_id,
        title=title,
        company_name=company_name,
        company_normalized_name=_normalize_comparison_key(company_name),
        location=_normalize_location(job.location),
        description=_normalize_description(job.description),
        apply_url=_normalize_url(job.apply_url),
        published_at=job.published_at,
        raw_payload=dict(job.raw_payload),
    )


def _normalize_required_text(value: str, *, field_name: str) -> str:
    cleaned = _normalize_optional_text(value)

    if cleaned is None:
        raise ValueError(f"{field_name} cannot be empty")

    return cleaned


def _normalize_optional_text(value: str | None) -> str | None:
    if value is None:
        return None

    cleaned = " ".join(value.split())

    return cleaned or None


def _normalize_comparison_key(value: str | None) -> str | None:
    if value is None:
        return None

    return value.casefold()


def _normalize_location(value: str | None) -> str | None:
    cleaned = _normalize_optional_text(value)

    if cleaned is None:
        return None

    cleaned = cleaned.rstrip(" ,")

    return cleaned or None


def _normalize_description(value: str | None) -> str | None:
    if value is None:
        return None

    cleaned = value.strip()

    return cleaned or None


def _normalize_url(value: str | None) -> str | None:
    if value is None:
        return None

    cleaned = value.strip()

    if not cleaned:
        return None

    parts = urlsplit(cleaned)

    if not parts.scheme or not parts.netloc:
        return cleaned

    path = parts.path

    if path not in ("", "/"):
        path = path.rstrip("/")

    return urlunsplit(
        (
            parts.scheme.lower(),
            parts.netloc.lower(),
            path,
            parts.query,
            "",
        )
    )
