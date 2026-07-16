import datetime

import pytest
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from server.app.database import Base
from server.app.db.orm import CandidateClip, InvestigationTimelineEntry
from server.app.main import app
from server.app.schemas import investigations as investigation_schemas
from server.app.schemas import reports as report_schemas


def _time(hour: int) -> datetime.datetime:
    return datetime.datetime(2026, 7, 17, hour, tzinfo=datetime.timezone.utc)


def test_investigation_routes_are_registered():
    route_paths = set(app.openapi()["paths"])

    assert {
        "/api/v1/investigations",
        "/api/v1/investigations/{investigation_id}/candidates",
        "/api/v1/investigations/{investigation_id}/timeline",
    } <= route_paths


@pytest.mark.parametrize(
    "schema_name",
    ["ReportCreate", "SearchAttributes"],
)
def test_time_windows_must_be_ordered(schema_name):
    schema = getattr(report_schemas, schema_name)

    with pytest.raises(ValidationError):
        schema(time_window_start=_time(12), time_window_end=_time(11))


def test_search_attributes_and_attribute_update_use_validated_defaults():
    first = report_schemas.SearchAttributes()
    second = report_schemas.SearchAttributes()

    first.camera_ids.append("camera-1")
    first.accessories.append("backpack")

    assert second.camera_ids == []
    assert second.accessories == []
    assert report_schemas.AttributeUpdate(
        attributes={"location": "Gate A"}
    ).attributes == report_schemas.SearchAttributes(
        location="Gate A",
    )


@pytest.mark.parametrize("verification_status", ["confirmed", "rejected"])
def test_candidate_update_accepts_terminal_verification_statuses(verification_status):
    update = investigation_schemas.CandidateUpdate(
        verification_status=verification_status,
        note="operator reviewed",
    )

    assert update.verification_status == verification_status
    assert update.note == "operator reviewed"


def test_candidate_update_rejects_unknown_verification_status():
    with pytest.raises(ValidationError):
        investigation_schemas.CandidateUpdate(verification_status="pending")


def test_vlm_result_validates_ranges_and_enums():
    result = investigation_schemas.VLMResult(
        supported_attributes=["red upper clothing"],
        contradicted_attributes=[],
        uncertainties=["face occluded"],
        relevant_start_seconds=1.5,
        relevant_end_seconds=3.0,
        match_recommendation="likely_match",
        source="gemini",
    )

    assert result.relevant_end_seconds == 3.0

    with pytest.raises(ValidationError):
        investigation_schemas.VLMResult(
            relevant_start_seconds=3.0,
            relevant_end_seconds=1.5,
            match_recommendation="possible_match",
            source="cached",
        )

    with pytest.raises(ValidationError):
        investigation_schemas.VLMResult(
            relevant_start_seconds=-1,
            match_recommendation="unknown",
            source="manual",
        )


def test_candidate_and_timeline_schemas_expose_evidence_fields():
    candidate = investigation_schemas.CandidateSchema(
        candidate_id="candidate-1",
        clip_id="clip-1",
        score=0.9,
        location="Gate A",
        clip_metadata={"duration_seconds": 8},
        vlm_result={"source": "cached"},
        media_available=True,
    )
    timeline = investigation_schemas.TimelineEntrySchema(
        id=1,
        location="Gate A",
        human_verified=True,
    )

    assert candidate.clip_id == "clip-1"
    assert candidate.location == "Gate A"
    assert candidate.clip_metadata == {"duration_seconds": 8}
    assert candidate.vlm_result == {"source": "cached"}
    assert candidate.media_available is True
    assert timeline.location == "Gate A"
    assert timeline.human_verified is True


def test_timeline_allows_at_most_one_entry_per_candidate():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        candidate = CandidateClip(investigation_id=1)
        session.add(candidate)
        session.commit()

        session.add_all(
            [
                InvestigationTimelineEntry(investigation_id=1, candidate_id=candidate.id),
                InvestigationTimelineEntry(investigation_id=1, candidate_id=candidate.id),
            ]
        )

        with pytest.raises(IntegrityError):
            session.commit()

    engine.dispose()
