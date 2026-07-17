import datetime
import uuid

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from ..database import Base


def _uid():
    return uuid.uuid4().hex[:12]


class Camera(Base):
    __tablename__ = "cameras"

    id = Column(Integer, primary_key=True, autoincrement=True)
    camera_id = Column(String(64), unique=True, nullable=False, default=_uid)
    name = Column(String(256), nullable=False)
    location = Column(String(256), default="")
    stream_source = Column(String(512), default="")
    status = Column(String(32), default="active")

    zones = relationship("Zone", back_populates="camera", cascade="all, delete-orphan")
    incidents = relationship("Incident", back_populates="camera_ref")


class Zone(Base):
    __tablename__ = "zones"

    id = Column(Integer, primary_key=True, autoincrement=True)
    zone_id = Column(String(64), unique=True, nullable=False, default=_uid)
    camera_id = Column(Integer, ForeignKey("cameras.id"), nullable=False)
    zone_type = Column(String(32), nullable=False)
    polygon = Column(JSON, nullable=False)
    capacity = Column(Integer, nullable=True)
    risk_multiplier = Column(Float, default=1.0)
    danger_direction = Column(JSON, nullable=True)

    camera = relationship("Camera", back_populates="zones")


class Playbook(Base):
    __tablename__ = "playbooks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(256), nullable=False)
    incident_type = Column(String(64), nullable=False)
    severity = Column(String(32), default="medium")
    actions = Column(JSON, nullable=False)
    escalation_condition = Column(String(512), default="")
    escalation_playbook_id = Column(Integer, nullable=True)


class Officer(Base):
    __tablename__ = "officers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    officer_id = Column(String(64), unique=True, nullable=False, default=_uid)
    name = Column(String(256), nullable=False)
    role = Column(String(128), default="Safety Officer")
    location = Column(String(256), default="")
    status = Column(String(32), default="available")

    assignments = relationship("Assignment", back_populates="officer")


class Incident(Base):
    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    incident_id = Column(String(64), unique=True, nullable=False, default=_uid)
    incident_type = Column(String(64), nullable=False)
    camera_id = Column(Integer, ForeignKey("cameras.id"), nullable=True)
    zone_id = Column(Integer, ForeignKey("zones.id"), nullable=True)
    severity = Column(String(16), default="low")
    risk_score = Column(Float, default=0.0)
    status = Column(String(32), default="detected")
    location = Column(String(256), default="")
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    description = Column(Text, default="")
    indicators = Column(JSON, default=dict)
    evidence = Column(JSON, default=dict)
    source_mode = Column(String(32), default="manual_demo")
    resolution_notes = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    camera_ref = relationship("Camera", back_populates="incidents")
    zone_ref = relationship("Zone")
    assignments = relationship("Assignment", back_populates="incident", cascade="all, delete-orphan")
    evidence_clips = relationship("EvidenceClip", back_populates="incident", cascade="all, delete-orphan")
    timeline_events = relationship("TimelineEvent", back_populates="incident", cascade="all, delete-orphan")


class EvidenceClip(Base):
    __tablename__ = "evidence_clips"

    id = Column(Integer, primary_key=True, autoincrement=True)
    incident_id = Column(Integer, ForeignKey("incidents.id"), nullable=False)
    camera_id = Column(String(64), default="")
    start_time = Column(Float, default=0.0)
    end_time = Column(Float, default=0.0)
    url = Column(String(512), default="")
    snapshot_url = Column(String(512), default="")

    incident = relationship("Incident", back_populates="evidence_clips")


class Assignment(Base):
    __tablename__ = "assignments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    assignment_id = Column(String(64), unique=True, nullable=False, default=_uid)
    incident_id = Column(Integer, ForeignKey("incidents.id"), nullable=False)
    officer_id = Column(Integer, ForeignKey("officers.id"), nullable=False)
    status = Column(String(32), default="assigned")
    notes = Column(Text, default="")
    assigned_at = Column(DateTime, default=datetime.datetime.utcnow)
    acknowledged_at = Column(DateTime, nullable=True)
    arrived_at = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True)

    incident = relationship("Incident", back_populates="assignments")
    officer = relationship("Officer", back_populates="assignments")


class TimelineEvent(Base):
    __tablename__ = "timeline_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    incident_id = Column(Integer, ForeignKey("incidents.id"), nullable=False)
    event_type = Column(String(64), nullable=False)
    description = Column(Text, default="")
    actor = Column(String(256), default="")
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    details = Column(JSON, default=dict)

    incident = relationship("Incident", back_populates="timeline_events")


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    report_id = Column(String(64), unique=True, nullable=False, default=_uid)
    reporter_type = Column(String(32), default="passenger")
    time_window_start = Column(DateTime, nullable=True)
    time_window_end = Column(DateTime, nullable=True)
    location = Column(String(256), default="")
    description = Column(Text, default="")
    direction = Column(String(256), default="")
    attributes = Column(JSON, default=dict)
    image_url = Column(String(512), default="")
    status = Column(String(32), default="submitted")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    investigation = relationship("Investigation", back_populates="report", uselist=False, cascade="all, delete-orphan")


class Investigation(Base):
    __tablename__ = "investigations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    investigation_id = Column(String(64), unique=True, nullable=False, default=_uid)
    report_id = Column(Integer, ForeignKey("reports.id"), nullable=False)
    search_filters = Column(JSON, default=dict)
    status = Column(String(32), default="pending")

    report = relationship("Report", back_populates="investigation")
    candidate_clips = relationship("CandidateClip", back_populates="investigation", cascade="all, delete-orphan")
    timeline_entries = relationship("InvestigationTimelineEntry", back_populates="investigation", cascade="all, delete-orphan")


class CandidateClip(Base):
    __tablename__ = "candidate_clips"

    id = Column(Integer, primary_key=True, autoincrement=True)
    candidate_id = Column(String(64), unique=True, nullable=False, default=_uid)
    clip_id = Column(String(64), default="")
    investigation_id = Column(Integer, ForeignKey("investigations.id"), nullable=False)
    score = Column(Float, default=0.0)
    explanation = Column(Text, default="")
    url = Column(String(512), nullable=True)
    snapshot_url = Column(String(512), nullable=True)
    camera_id = Column(String(64), default="")
    location = Column(String(256), default="")
    clip_metadata = Column(JSON, default=dict)
    vlm_result = Column(JSON, nullable=True, default=None)
    timestamp = Column(DateTime, nullable=True)
    verification_status = Column(String(32), default="pending")

    investigation = relationship("Investigation", back_populates="candidate_clips")


class InvestigationTimelineEntry(Base):
    __tablename__ = "investigation_timeline_entries"
    __table_args__ = (
        UniqueConstraint("candidate_id", name="uq_investigation_timeline_entries_candidate_id"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    investigation_id = Column(Integer, ForeignKey("investigations.id"), nullable=False)
    candidate_id = Column(Integer, ForeignKey("candidate_clips.id"), nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    camera_id = Column(String(64), default="")
    location = Column(String(256), default="")
    note = Column(Text, default="")
    sort_order = Column(Integer, default=0)

    investigation = relationship("Investigation", back_populates="timeline_entries")


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    entity_type = Column(String(64), nullable=False)
    entity_id = Column(String(64), default="")
    action = Column(String(64), nullable=False)
    actor = Column(String(256), default="operator")
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    details = Column(JSON, default=dict)
