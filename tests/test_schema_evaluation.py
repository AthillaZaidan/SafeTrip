import json
import tempfile
import unittest
from pathlib import Path

from transitshield_vision.evaluation import GroundTruthEvent, evaluate_events, temporal_iou
from transitshield_vision.evidence import evidence_paths
from transitshield_vision.incident_export import write_incidents
from transitshield_vision.schemas import Incident


class SchemaAndEvaluationTests(unittest.TestCase):
    def test_incident_is_plain_json_and_optional_end_is_null(self):
        incident = Incident(
            incident_id="INC_CAM_000001",
            incident_type="restricted_zone_intrusion",
            camera_id="CAM",
            zone_id="ZONE",
            entity_ids=["track:1"],
            timestamp_start_seconds=1.0,
            timestamp_detected_seconds=2.0,
            timestamp_end_seconds=None,
            duration_seconds=1.0,
            detection_confidence=0.9,
            indicators={"inside_restricted_zone": True},
            evidence={"snapshot_raw": None, "snapshot_annotated": None, "clip": None, "metadata": None},
            source_mode="cached_ai",
        )
        payload = incident.to_dict()
        self.assertIsNone(payload["timestamp_end_seconds"])
        json.dumps(payload)

    def test_incident_export_validates_before_write(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "incidents.json"
            with self.assertRaises(ValueError):
                write_incidents([{"incident_type": "unknown"}], path)
            self.assertFalse(path.exists())

    def test_evidence_paths_are_deterministic_and_relative(self):
        paths = evidence_paths("INC_CAM_000001")
        self.assertEqual(paths["clip"], "outputs/incidents/INC_CAM_000001/evidence.mp4")

    def test_temporal_iou_and_false_alert_count_by_event(self):
        self.assertAlmostEqual(temporal_iou(0, 4, 2, 6), 2 / 6)
        truth = [GroundTruthEvent("restricted_zone_intrusion", "CAM", "ZONE", 0, 4)]
        predictions = [
            {"incident_type": "restricted_zone_intrusion", "camera_id": "CAM", "zone_id": "ZONE", "timestamp_start_seconds": 1, "timestamp_detected_seconds": 2, "timestamp_end_seconds": 3},
            {"incident_type": "restricted_zone_intrusion", "camera_id": "CAM", "zone_id": "ZONE", "timestamp_start_seconds": 10, "timestamp_detected_seconds": 10, "timestamp_end_seconds": 11},
        ]
        metrics = evaluate_events(predictions, truth, duration_hours=1.0, iou_threshold=0.1)
        self.assertEqual(metrics["true_positives"], 1)
        self.assertEqual(metrics["false_alerts"], 1)
        self.assertEqual(metrics["false_alerts_per_camera_hour"], 1.0)


if __name__ == "__main__":
    unittest.main()
