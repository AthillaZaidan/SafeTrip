import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.database import Base, ENGINE, SessionLocal
from app.db.orm import Camera, Officer, Playbook, Zone

DB_PATH = Path(__file__).resolve().parent / "data" / "transitshield.db"

DEMO_CAMERAS = [
    {
        "camera_id": "CAM_PLATFORM_B_01",
        "name": "Platform B Camera 01",
        "location": "Platform B, South Entrance",
        "stream_source": "data/demo-videos/platform_b_demo.mp4",
        "status": "active",
        "zones": [
            {"zone_id": "ZONE_TRACK_BOUNDARY", "zone_type": "restricted", "polygon": [[40, 330], [600, 330], [635, 475], [5, 475]], "capacity": None, "risk_multiplier": 1.5, "danger_direction": [0.0, 1.0]},
            {"zone_id": "ZONE_RAILWAY_TRACK", "zone_type": "track_area", "polygon": [[55, 365], [585, 365], [625, 475], [15, 475]], "capacity": None, "risk_multiplier": 1.8, "danger_direction": None},
            {"zone_id": "ZONE_GATE_QUEUE", "zone_type": "crowd_monitoring", "polygon": [[120, 100], [520, 100], [565, 325], [85, 325]], "capacity": 18, "risk_multiplier": 1.3, "danger_direction": None},
            {"zone_id": "ZONE_NORMAL", "zone_type": "normal", "polygon": [[20, 20], [620, 20], [600, 325], [40, 325]], "capacity": None, "risk_multiplier": 1.0, "danger_direction": None},
        ],
    },
    {
        "camera_id": "CAM_CONCOURSE_A_01",
        "name": "Concourse A Camera 01",
        "location": "Concourse A, Main Corridor",
        "stream_source": "data/demo-videos/concourse_a_demo.mp4",
        "status": "active",
        "zones": [
            {"zone_id": "ZONE_CONCOURSE_FLOW", "zone_type": "crowd_monitoring", "polygon": [[50, 50], [550, 50], [570, 370], [30, 370]], "capacity": 30, "risk_multiplier": 1.2, "danger_direction": None},
            {"zone_id": "ZONE_EXIT_CORRIDOR", "zone_type": "limited_dwell", "polygon": [[380, 60], [580, 60], [600, 280], [360, 280]], "capacity": None, "risk_multiplier": 1.4, "danger_direction": [1.0, 0.0]},
        ],
    },
]

DEMO_OFFICERS = [
    {"officer_id": "OFF_001", "name": "Rina Wahyuni", "role": "Safety Officer", "location": "Platform B, North Gate", "status": "available"},
    {"officer_id": "OFF_002", "name": "Budi Santoso", "role": "Senior Safety Officer", "location": "Concourse A, Information Desk", "status": "available"},
    {"officer_id": "OFF_003", "name": "Dewi Lestari", "role": "Safety Officer", "location": "Platform B, South Entrance", "status": "available"},
    {"officer_id": "OFF_004", "name": "Agus Wijaya", "role": "Field Supervisor", "location": "Control Room, Terminal 1", "status": "available"},
    {"officer_id": "OFF_005", "name": "Siti Nurhaliza", "role": "Safety Officer", "location": "Concourse A, East Wing", "status": "available"},
]

DEMO_PLAYBOOKS = [
    {
        "name": "Restricted Zone Intrusion — Standard",
        "incident_type": "restricted_zone_intrusion",
        "severity": "medium",
        "actions": ["Dispatch nearest safety officer", "Activate local warning announcement", "Notify control room supervisor", "Monitor subject movement"],
        "escalation_condition": "Subject approaches active vehicle path or fails to leave restricted zone within 60 seconds",
    },
    {
        "name": "Restricted Zone Intrusion — Critical",
        "incident_type": "restricted_zone_intrusion",
        "severity": "high",
        "actions": ["Dispatch nearest safety officer (priority)", "Activate emergency alarm", "Notify control room supervisor", "Halt approaching vehicle if possible", "Alert all platform personnel"],
        "escalation_condition": "Subject enters track area or active vehicle path",
    },
    {
        "name": "Person Down — Standard",
        "incident_type": "possible_person_down",
        "severity": "medium",
        "actions": ["Dispatch nearest safety officer with medical kit", "Assess need for medical emergency services", "Secure area around the person", "Document incident with camera snapshot", "Notify station manager"],
        "escalation_condition": "Person unresponsive, bleeding, or in immediate danger",
    },
    {
        "name": "Person Down — Critical",
        "incident_type": "possible_person_down",
        "severity": "high",
        "actions": ["Dispatch nearest safety officer (emergency)", "Call emergency medical services immediately", "Clear area of bystanders", "Provide first aid until medical help arrives", "Securely record and document all evidence"],
        "escalation_condition": "Medical emergency, unresponsive person, or dangerous environment",
    },
    {
        "name": "Crowd Compression — Standard",
        "incident_type": "crowd_compression",
        "severity": "low",
        "actions": ["Monitor crowd density trend", "Assess gate or barrier status", "Notify station manager if density continues increasing"],
        "escalation_condition": "Density exceeds 85% of zone capacity or continues increasing for 5+ minutes",
    },
    {
        "name": "Crowd Compression — Critical",
        "incident_type": "crowd_compression",
        "severity": "high",
        "actions": ["Dispatch multiple safety officers to zone", "Activate crowd control barriers", "Redirect incoming passenger flow", "Announce crowd control instructions", "Consider temporary gate closure"],
        "escalation_condition": "Density exceeds 95% capacity or crowd movement stops completely",
    },
]

Base.metadata.create_all(bind=ENGINE)


def seed():
    db = SessionLocal()
    try:
        db.query(Zone).delete()
        db.query(Camera).delete()
        db.query(Officer).delete()
        db.query(Playbook).delete()
        db.commit()

        for cam_data in DEMO_CAMERAS:
            zones_data = cam_data.pop("zones")
            camera = Camera(**cam_data)
            db.add(camera)
            db.flush()
            for z in zones_data:
                db.add(Zone(camera_id=camera.id, **z))

        for o in DEMO_OFFICERS:
            db.add(Officer(**o))

        for p in DEMO_PLAYBOOKS:
            db.add(Playbook(**p))

        db.commit()
        print(f"Seeded {len(DEMO_CAMERAS)} cameras, {len(DEMO_OFFICERS)} officers, {len(DEMO_PLAYBOOKS)} playbooks")
        print(f"Database: {DB_PATH.resolve()}")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
