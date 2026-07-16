from __future__ import annotations

import datetime
from typing import Optional

from sqlalchemy.orm import Session

from ..db.orm import AuditEvent, Assignment, EvidenceClip, Incident, Officer, TimelineEvent


class IncidentService:
    SEVERITY_ORDER = {"low": 0, "medium": 1, "high": 2, "critical": 3}

    def __init__(self, db: Session):
        self.db = db

    def list_incidents(self, status: Optional[str] = None, severity: Optional[str] = None) -> list[Incident]:
        q = self.db.query(Incident)
        if status:
            q = q.filter(Incident.status == status)
        if severity:
            q = q.filter(Incident.severity == severity)
        return q.order_by(Incident.created_at.desc()).all()

    def get_incident(self, incident_id: str) -> Optional[Incident]:
        return self.db.query(Incident).filter(Incident.incident_id == incident_id).first()

    def create_incident(self, data: dict) -> Incident:
        incident = Incident(
            incident_type=data.get("incident_type", "unknown"),
            camera_id=data.get("camera_id"),
            zone_id=data.get("zone_id"),
            severity=data.get("severity", "low"),
            risk_score=data.get("risk_score", 0.0),
            status="detected",
            location=data.get("location", ""),
            description=data.get("description", ""),
            indicators=data.get("indicators", {}),
            evidence=data.get("evidence", {}),
            source_mode=data.get("source_mode", "manual_demo"),
        )
        self.db.add(incident)
        self.db.flush()
        self._add_timeline(incident, "incident_created", f"Incident {incident.incident_type} detected")
        self._audit("incident", incident.incident_id, "created")
        self.db.commit()
        return incident

    def update_incident(self, incident_id: str, data: dict) -> Optional[Incident]:
        incident = self.get_incident(incident_id)
        if not incident:
            return None
        for field in ("severity", "status", "description", "resolution_notes"):
            if field in data and data[field] is not None:
                setattr(incident, field, data[field])
        incident.updated_at = datetime.datetime.utcnow()
        self._audit("incident", incident_id, "updated", data)
        self.db.commit()
        return incident

    def get_evidence(self, incident_id: str) -> list[EvidenceClip]:
        incident = self.get_incident(incident_id)
        if not incident:
            return []
        return self.db.query(EvidenceClip).filter(EvidenceClip.incident_id == incident.id).all()

    def get_timeline(self, incident_id: str) -> list[TimelineEvent]:
        incident = self.get_incident(incident_id)
        if not incident:
            return []
        return (
            self.db.query(TimelineEvent)
            .filter(TimelineEvent.incident_id == incident.id)
            .order_by(TimelineEvent.timestamp.asc())
            .all()
        )

    def assign_officer(self, incident_id: str, officer_id: str) -> Optional[dict]:
        incident = self.get_incident(incident_id)
        officer = self.db.query(Officer).filter(Officer.officer_id == officer_id).first()
        if not incident or not officer:
            return None
        assignment = Assignment(
            incident_id=incident.id,
            officer_id=officer.id,
            status="assigned",
        )
        self.db.add(assignment)
        officer.status = "assigned"
        incident.status = "assigned"
        incident.updated_at = datetime.datetime.utcnow()
        self._add_timeline(incident, "officer_assigned", f"Officer {officer.name} assigned")
        self._audit("assignment", assignment.assignment_id, "created")
        self.db.commit()
        return {
            "assignment_id": assignment.assignment_id,
            "incident_id": incident_id,
            "officer_id": officer_id,
            "officer_name": officer.name,
            "status": "assigned",
        }

    def update_assignment(self, assignment_id: str, status: str, notes: str = "") -> Optional[dict]:
        assignment = self.db.query(Assignment).filter(Assignment.assignment_id == assignment_id).first()
        if not assignment:
            return None
        assignment.status = status
        if notes:
            assignment.notes = notes
        now = datetime.datetime.utcnow()
        if status == "acknowledged":
            assignment.acknowledged_at = now
        elif status == "arrived":
            assignment.arrived_at = now
        elif status in ("resolved", "escalated"):
            assignment.resolved_at = now
            incident = assignment.incident
            incident.status = status
            incident.updated_at = now
            if status == "resolved":
                self._add_timeline(incident, "incident_resolved", "Incident resolved")
                if assignment.officer:
                    assignment.officer.status = "available"
        self._audit("assignment", assignment_id, status)
        self.db.commit()
        return {
            "assignment_id": assignment_id,
            "status": status,
            "notes": notes,
        }

    def approve_playbook(self, incident_id: str, playbook_id: int) -> Optional[Incident]:
        incident = self.get_incident(incident_id)
        if not incident:
            return None
        self._add_timeline(incident, "playbook_approved", f"Playbook {playbook_id} approved")
        self._audit("incident", incident_id, "playbook_approved", {"playbook_id": playbook_id})
        self.db.commit()
        return incident

    def _add_timeline(self, incident: Incident, event_type: str, description: str):
        self.db.add(TimelineEvent(
            incident_id=incident.id,
            event_type=event_type,
            description=description,
            timestamp=datetime.datetime.utcnow(),
        ))

    def _audit(self, entity_type: str, entity_id: str, action: str, details: dict = None):
        self.db.add(AuditEvent(
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            details=details or {},
            timestamp=datetime.datetime.utcnow(),
        ))
