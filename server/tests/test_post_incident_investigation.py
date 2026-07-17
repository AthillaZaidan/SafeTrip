import datetime

import pytest
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from server.app.database import Base
from server.app.db.orm import (
    CandidateClip,
    Investigation,
    InvestigationTimelineEntry,
    Report,
)
from server.app.main import app
from server.app.routes.reports import update_attributes
from server.app.schemas import investigations as investigation_schemas
from server.app.schemas import reports as report_schemas
from server.app.services.investigation_service import InvestigationService


def _time(hour: int) -> datetime.datetime:
    return datetime.datetime(2026, 7, 17, hour, tzinfo=datetime.timezone.utc)


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        yield session

    engine.dispose()


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


def test_report_create_rejects_mixed_naive_and_aware_time_window():
    with pytest.raises(ValidationError):
        report_schemas.ReportCreate(
            time_window_start=datetime.datetime(2026, 7, 17, 10),
            time_window_end=_time(11),
        )


def test_search_attributes_rejects_mixed_naive_and_aware_time_window():
    with pytest.raises(ValidationError):
        report_schemas.SearchAttributes(
            time_window_start=_time(10),
            time_window_end=datetime.datetime(2026, 7, 17, 11),
        )


@pytest.mark.parametrize("schema", [report_schemas.ReportCreate, report_schemas.SearchAttributes])
def test_time_windows_allow_matching_timezone_awareness(schema):
    assert schema(
        time_window_start=datetime.datetime(2026, 7, 17, 10),
        time_window_end=datetime.datetime(2026, 7, 17, 11),
    )
    assert schema(time_window_start=_time(10), time_window_end=_time(11))


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


def test_update_attributes_route_persists_plain_json(db_session):
    report = Report(report_id="report-json")
    db_session.add(report)
    db_session.commit()

    data = report_schemas.AttributeUpdate(
        attributes={
            "location": "Gate A",
            "time_window_start": _time(10),
            "time_window_end": _time(11),
        }
    )

    update_attributes("report-json", data, db_session)
    db_session.expire_all()
    persisted = db_session.query(Report).filter_by(report_id="report-json").one()

    assert isinstance(persisted.attributes, dict)
    assert persisted.attributes["location"] == "Gate A"
    assert isinstance(persisted.attributes["time_window_start"], str)


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


def test_vlm_result_accepts_valid_evidence():
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


def test_vlm_result_rejects_reversed_relevant_range():
    with pytest.raises(ValidationError):
        investigation_schemas.VLMResult(
            relevant_start_seconds=3.0,
            relevant_end_seconds=1.5,
            match_recommendation="possible_match",
            source="cached",
        )


def test_vlm_result_rejects_negative_relevant_timestamp():
    with pytest.raises(ValidationError):
        investigation_schemas.VLMResult(
            relevant_start_seconds=-1,
            match_recommendation="unlikely_match",
            source="fallback",
        )


def test_vlm_result_rejects_unknown_match_recommendation():
    with pytest.raises(ValidationError):
        investigation_schemas.VLMResult(
            match_recommendation="unknown",
            source="cached",
        )


def test_vlm_result_rejects_unknown_source():
    with pytest.raises(ValidationError):
        investigation_schemas.VLMResult(
            match_recommendation="possible_match",
            source="manual",
        )


def test_candidate_and_timeline_schemas_expose_evidence_fields():
    candidate = investigation_schemas.CandidateSchema(
        candidate_id="candidate-1",
        clip_id="clip-1",
        score=0.9,
        location="Gate A",
        clip_metadata={"duration_seconds": 8},
        vlm_result={
            "supported_attributes": ["red upper clothing"],
            "contradicted_attributes": [],
            "uncertainties": ["face occluded"],
            "relevant_start_seconds": 1.5,
            "relevant_end_seconds": 3.0,
            "match_recommendation": "likely_match",
            "source": "cached",
        },
        url=None,
        snapshot_url=None,
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
    assert isinstance(candidate.vlm_result, investigation_schemas.VLMResult)
    assert candidate.vlm_result.source == "cached"
    assert candidate.url is None
    assert candidate.snapshot_url is None
    assert candidate.media_available is True
    assert timeline.location == "Gate A"
    assert timeline.human_verified is True


def test_persisted_candidate_without_vlm_result_validates_as_none(db_session):
    candidate = CandidateClip(
        candidate_id="candidate-without-vlm",
        investigation_id=1,
    )
    db_session.add(candidate)
    db_session.commit()
    db_session.expire_all()

    persisted = (
        db_session.query(CandidateClip)
        .filter_by(candidate_id="candidate-without-vlm")
        .one()
    )
    validated = investigation_schemas.CandidateSchema.model_validate(persisted)

    assert persisted.vlm_result is None
    assert validated.vlm_result is None


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


def test_confirming_candidate_twice_keeps_one_timeline_entry(db_session):
    report = Report(report_id="report-confirm")
    investigation = Investigation(
        investigation_id="investigation-confirm",
        report=report,
    )
    candidate = CandidateClip(
        candidate_id="candidate-confirm",
        investigation=investigation,
        score=0.9,
        camera_id="camera-1",
    )
    db_session.add(candidate)
    db_session.commit()

    service = InvestigationService(db_session)
    service.update_candidate(
        "investigation-confirm",
        "candidate-confirm",
        "confirmed",
    )
    service.update_candidate(
        "investigation-confirm",
        "candidate-confirm",
        "confirmed",
    )

    assert (
        db_session.query(InvestigationTimelineEntry)
        .filter_by(candidate_id=candidate.id)
        .count()
        == 1
    )
