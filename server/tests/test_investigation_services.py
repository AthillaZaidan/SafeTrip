import datetime

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from server.app.database import Base
from server.app.db.orm import AuditEvent, InvestigationTimelineEntry
from server.app.routes.investigations import (
    create_investigation as create_investigation_route,
)
from server.app.routes.investigations import (
    get_investigation_timeline as get_timeline_route,
)
from server.app.routes.investigations import list_candidates as list_candidates_route
from server.app.routes.investigations import update_candidate as update_candidate_route
from server.app.schemas.investigations import CandidateUpdate, InvestigationCreate
from server.app.schemas.reports import SearchAttributes
from server.app.services.investigation_ai import InvestigationAI
from server.app.services.investigation_service import (
    InvestigationService,
    ReportNotReadyError,
)
from server.app.services.report_service import ReportService


JAKARTA = datetime.timezone(datetime.timedelta(hours=7))


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    engine.dispose()


def _report_data(description=None):
    return {
        "reporter_type": "passenger",
        "time_window_start": datetime.datetime(
            2026, 7, 17, 17, 9, tzinfo=JAKARTA
        ),
        "time_window_end": datetime.datetime(
            2026, 7, 17, 17, 11, 59, tzinfo=JAKARTA
        ),
        "location": "",
        "description": description
        or "Orang berjaket abu-abu dan membawa tas hitam berlari menuju Exit D.",
        "direction": "toward Exit D",
    }


def _create_confirmed_investigation(db_session):
    report_service = ReportService(db_session, ai=InvestigationAI(env={}))
    report = report_service.create_report(_report_data())
    extracted = report_service.extract_attributes(report.report_id)
    report_service.update_attributes(
        report.report_id,
        SearchAttributes.model_validate(extracted).model_dump(mode="json"),
    )
    service = InvestigationService(db_session, ai=InvestigationAI(env={}))
    investigation = service.create_investigation(report.report_id)
    return service, investigation, service.list_candidates(
        investigation.investigation_id
    )


def test_cached_service_flow_persists_ranked_vlm_candidates(db_session):
    report_service = ReportService(db_session, ai=InvestigationAI(env={}))
    report = report_service.create_report(_report_data())

    assert report.report_id
    created_audit = db_session.query(AuditEvent).filter_by(action="created").one()
    assert created_audit.entity_id == report.report_id

    extracted = report_service.extract_attributes(report.report_id)

    assert extracted["extraction_source"] == "cached"
    assert extracted["upper_clothing"] == "grey jacket"
    assert extracted["accessories"] == ["black backpack"]
    corrected = SearchAttributes.model_validate(extracted).model_dump(mode="json")
    confirmed = report_service.update_attributes(report.report_id, corrected)
    assert confirmed.status == "attributes_confirmed"
    assert confirmed.attributes["extraction_source"] == "cached"

    investigation = InvestigationService(
        db_session,
        ai=InvestigationAI(env={}),
    ).create_investigation(report.report_id)
    candidates = InvestigationService(db_session).list_candidates(
        investigation.investigation_id
    )

    assert investigation.status == "awaiting_review"
    assert len(candidates) == 5
    assert [candidate.clip_id for candidate in candidates[:3]] == [
        "CLIP-TA-001",
        "CLIP-TA-004",
        "CLIP-TA-007",
    ]
    assert all(candidate.vlm_result["source"] == "cached" for candidate in candidates)
    assert all(candidate.url is None for candidate in candidates)
    assert all(
        candidate.clip_metadata["media_available"] is False
        for candidate in candidates
    )
    assert all(candidate.clip_metadata["matched_attributes"] for candidate in candidates)


def test_report_without_demo_match_uses_honest_extraction_fallback(db_session):
    service = ReportService(db_session, ai=InvestigationAI(env={}))
    report = service.create_report(_report_data("Dompet saya hilang di dalam kereta."))

    extracted = service.extract_attributes(report.report_id)

    assert extracted["extraction_source"] == "fallback"
    assert extracted["upper_clothing"] == ""
    assert extracted["accessories"] == []
    assert extracted["direction"] == "toward Exit D"


def test_unconfirmed_report_cannot_start_investigation(db_session):
    report = ReportService(db_session).create_report(_report_data())

    with pytest.raises(ReportNotReadyError):
        InvestigationService(db_session).create_investigation(report.report_id)

    with pytest.raises(HTTPException) as error:
        create_investigation_route(
            InvestigationCreate(report_id=report.report_id),
            db_session,
        )
    assert error.value.status_code == 409


def test_investigation_routes_return_404_for_missing_resources(db_session):
    with pytest.raises(HTTPException) as create_error:
        create_investigation_route(
            InvestigationCreate(report_id="missing-report"),
            db_session,
        )
    assert create_error.value.status_code == 404

    with pytest.raises(HTTPException) as candidates_error:
        list_candidates_route("missing-investigation", db_session)
    assert candidates_error.value.status_code == 404


def test_candidate_route_exposes_metadata_vlm_and_truthful_media_state(db_session):
    report_service = ReportService(db_session, ai=InvestigationAI(env={}))
    report = report_service.create_report(_report_data())
    extracted = report_service.extract_attributes(report.report_id)
    report_service.update_attributes(
        report.report_id,
        SearchAttributes.model_validate(extracted).model_dump(mode="json"),
    )
    investigation = InvestigationService(
        db_session,
        ai=InvestigationAI(env={}),
    ).create_investigation(report.report_id)

    candidates = list_candidates_route(investigation.investigation_id, db_session)

    first = candidates[0]
    assert first.clip_id == "CLIP-TA-001"
    assert first.location == "Lantai 1 Concourse"
    assert first.vlm_result.source == "cached"
    assert first.media_available is False
    assert first.url is None


def test_candidate_review_is_scoped_to_its_investigation(db_session):
    service, first_investigation, first_candidates = (
        _create_confirmed_investigation(db_session)
    )
    _, second_investigation, _ = _create_confirmed_investigation(db_session)
    candidate = first_candidates[0]

    result = service.update_candidate(
        second_investigation.investigation_id,
        candidate.candidate_id,
        "confirmed",
        note="wrong investigation",
    )

    assert result is None
    assert candidate.verification_status == "pending"
    assert db_session.query(InvestigationTimelineEntry).count() == 0
    assert first_investigation.status == "awaiting_review"

    with pytest.raises(HTTPException) as error:
        update_candidate_route(
            second_investigation.investigation_id,
            candidate.candidate_id,
            CandidateUpdate(
                verification_status="confirmed",
                note="wrong investigation",
            ),
            db_session,
        )
    assert error.value.status_code == 404


def test_rejection_removes_prior_timeline_entry_idempotently(db_session):
    service, investigation, candidates = _create_confirmed_investigation(db_session)
    candidate = candidates[0]

    service.update_candidate(
        investigation.investigation_id,
        candidate.candidate_id,
        "confirmed",
        note="Matches the passenger report",
    )
    entry = db_session.query(InvestigationTimelineEntry).one()
    assert entry.note == "Matches the passenger report"
    assert entry.location == "Lantai 1 Concourse"

    service.update_candidate(
        investigation.investigation_id,
        candidate.candidate_id,
        "rejected",
        note="Operator rejected after closer review",
    )
    service.update_candidate(
        investigation.investigation_id,
        candidate.candidate_id,
        "rejected",
    )

    assert candidate.verification_status == "rejected"
    assert db_session.query(InvestigationTimelineEntry).count() == 0


def test_confirmed_timeline_is_chronological_and_human_verified(db_session):
    service, investigation, candidates = _create_confirmed_investigation(db_session)
    by_clip = {candidate.clip_id: candidate for candidate in candidates}

    service.update_candidate(
        investigation.investigation_id,
        by_clip["CLIP-TA-007"].candidate_id,
        "confirmed",
        note="Seen near Exit D",
    )
    service.update_candidate(
        investigation.investigation_id,
        by_clip["CLIP-TA-001"].candidate_id,
        "confirmed",
        note="First seen at concourse",
    )

    timeline = get_timeline_route(investigation.investigation_id, db_session)

    assert [entry.location for entry in timeline] == [
        "Lantai 1 Concourse",
        "Exit D Link",
    ]
    assert [entry.note for entry in timeline] == [
        "First seen at concourse",
        "Seen near Exit D",
    ]
    assert [entry.sort_order for entry in timeline] == [0, 1]
    assert all(entry.human_verified for entry in timeline)
    assert investigation.status == "in_progress"


def test_review_completes_only_after_every_candidate_is_decided(db_session):
    service, investigation, candidates = _create_confirmed_investigation(db_session)

    service.update_candidate(
        investigation.investigation_id,
        candidates[0].candidate_id,
        "confirmed",
    )
    assert investigation.status == "in_progress"

    for candidate in candidates[1:]:
        service.update_candidate(
            investigation.investigation_id,
            candidate.candidate_id,
            "rejected",
        )

    assert investigation.status == "review_complete"
    assert db_session.query(InvestigationTimelineEntry).count() == 1


def test_timeline_route_returns_404_for_unknown_investigation(db_session):
    with pytest.raises(HTTPException) as error:
        get_timeline_route("missing-investigation", db_session)

    assert error.value.status_code == 404
