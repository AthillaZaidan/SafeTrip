import json
import tempfile
import unittest
from pathlib import Path

from transitshield_vision.evaluation import GroundTruthEvent, evaluate_by_event_type, evaluate_events, temporal_iou
from transitshield_vision.evidence import EvidenceFrame, evidence_paths, write_evidence
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

    def test_evidence_writer_creates_four_reviewable_artifacts(self):
        class Frame:
            shape = (10, 20, 3)

        class VideoWriter:
            def __init__(self, path, *_args):
                self.path = Path(path)
                self.frames = []

            def isOpened(self):
                return True

            def write(self, frame):
                self.frames.append(frame)

            def release(self):
                self.path.write_bytes(b"video")

        class CV2:
            @staticmethod
            def imwrite(path, _frame):
                Path(path).write_bytes(b"image")
                return True

            @staticmethod
            def VideoWriter(path, *_args):
                return VideoWriter(path, *_args)

            @staticmethod
            def VideoWriter_fourcc(*_args):
                return 0

        incident = Incident(
            "INC_CAM_000001", "person_running_on_track", "CAM", "TRACK", ["track:1"],
            1, 2, None, 1, 0.9, {"normalized_speed": 1.2},
            {"snapshot_raw": None, "snapshot_annotated": None, "clip": None, "metadata": None}, "full_ai",
        )
        with tempfile.TemporaryDirectory() as directory:
            paths = write_evidence(
                incident,
                [EvidenceFrame(1, Frame(), Frame()), EvidenceFrame(2, Frame(), Frame()), EvidenceFrame(3, Frame(), Frame())],
                fps=1,
                root=directory,
                cv2_module=CV2,
            )
            self.assertTrue(all(Path(path).is_file() for path in paths.values()))
            metadata = json.loads(Path(paths["metadata"]).read_text(encoding="utf-8"))
            self.assertEqual(metadata["incident_id"], "INC_CAM_000001")

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

    def test_metrics_are_reported_for_every_supported_event(self):
        metrics = evaluate_by_event_type([], [], duration_hours=1.0)
        self.assertEqual(
            set(metrics),
            {"restricted_zone_intrusion", "person_running_on_track", "possible_person_down", "crowd_compression"},
        )


if __name__ == "__main__":
    unittest.main()
