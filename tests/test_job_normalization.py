import pytest

from app.integrations.job_sources.base import ExternalJobDTO
from app.services.job_normalization import normalize_external_job


def test_normalize_external_job_cleans_safe_fields() -> None:
    raw_payload = {
        "position": "  Projectpedia   Team Member ",
        "location": " Narmada, ",
    }

    job = ExternalJobDTO(
        external_id=" 1132651 ",
        title="  Projectpedia   Team Member ",
        company_name="  OpenAI  ",
        location=" Narmada, ",
        description="  <p>Python   backend role</p>  ",
        apply_url=" HTTPS://RemoteOK.com/remote-jobs/example/#top ",
        raw_payload=raw_payload,
    )

    normalized = normalize_external_job(job)

    assert normalized.external_id == "1132651"
    assert normalized.title == "Projectpedia Team Member"
    assert normalized.company_name == "OpenAI"
    assert normalized.company_normalized_name == "openai"
    assert normalized.location == "Narmada"
    assert normalized.description == "<p>Python   backend role</p>"
    assert normalized.apply_url == "https://remoteok.com/remote-jobs/example"
    assert normalized.raw_payload == raw_payload


def test_normalize_external_job_converts_empty_optional_text_to_none() -> None:
    job = ExternalJobDTO(
        external_id="job-1",
        title="Python Developer",
        company_name="   ",
        location=" , ",
        description="   ",
        apply_url="   ",
    )

    normalized = normalize_external_job(job)

    assert normalized.company_name is None
    assert normalized.company_normalized_name is None
    assert normalized.location is None
    assert normalized.description is None
    assert normalized.apply_url is None


def test_normalize_external_job_preserves_query_parameters_and_removes_fragment() -> None:
    job = ExternalJobDTO(
        external_id="job-2",
        title="Backend Developer",
        apply_url="https://Example.com/apply/?job_id=123#form",
    )

    normalized = normalize_external_job(job)

    assert normalized.apply_url == "https://example.com/apply?job_id=123"


def test_normalize_external_job_rejects_whitespace_only_required_title() -> None:
    job = ExternalJobDTO(
        external_id="job-3",
        title="   ",
    )

    with pytest.raises(ValueError, match="title cannot be empty"):
        normalize_external_job(job)


def test_normalize_external_job_copies_raw_payload() -> None:
    raw_payload = {"position": "Python Developer"}

    job = ExternalJobDTO(
        external_id="job-4",
        title="Python Developer",
        raw_payload=raw_payload,
    )

    normalized = normalize_external_job(job)

    assert normalized.raw_payload == raw_payload
    assert normalized.raw_payload is not raw_payload
