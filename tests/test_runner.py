import json
import tempfile
import unittest
from pathlib import Path

from transitshield_vision.config import parse_camera_config, parse_event_rules, parse_runtime_config
from transitshield_vision.runner import run_pipeline
from transitshield_vision.schemas import Incident


class RunnerTests(unittest.TestCase):
    def setUp(self):
        self.camera = parse_camera_config(
            {
                "camera_id": "CAM",
                "video_path": "unused.mp4",
                "zones": [{"zone_id": "R", "zone_type": "restricted", "polygon": [[0, 0], [10, 0], [10, 10], [0, 10]]}],
            },
            require_video=False,
        )
        self.rules = parse_event_rules(
            {
                "restricted_zone_intrusion": {"minimum_duration_seconds": 1, "cooldown_seconds": 5},
                "person_running_on_track": {"minimum_duration_seconds": 1, "cooldown_seconds": 5, "minimum_normalized_speed": 1},
                "possible_person_down": {"minimum_duration_seconds": 1, "cooldown_seconds": 5, "minimum_aspect_ratio": 2, "maximum_normalized_speed": 0.01},
                "crowd_compression": {"minimum_duration_seconds": 1, "cooldown_seconds": 5, "minimum_density_ratio": 1, "minimum_density_growth": 1, "maximum_average_normalized_speed": 0},
            }
        )

    def test_cached_run_exports_incidents_and_summary(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            cache = root / "cache.jsonl"
            cache.write_text(
                '\n'.join([
                    json.dumps({"frame_index": 0, "timestamp_seconds": 0, "tracks": [{"track_id": 1, "confidence": 0.9, "bbox_xyxy": [3, 0, 7, 10]}]}),
                    json.dumps({"frame_index": 1, "timestamp_seconds": 1, "tracks": [{"track_id": 1, "confidence": 0.9, "bbox_xyxy": [3, 0, 7, 10]}]}),
                ]),
                encoding="utf-8",
            )
            result = run_pipeline(parse_runtime_config({"execution_mode": "cached_ai"}), self.camera, self.rules, output_root=root / "out", cache_path=cache)
            self.assertEqual(result.summary["incident_counts"]["restricted_zone_intrusion"], 1)
            self.assertTrue((root / "out" / "incidents.json").is_file())
            self.assertTrue((root / "out" / "pipeline_summary.json").is_file())

    def test_manual_mode_requires_explicit_manual_source_mode(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            incident = Incident("INC_CAM_1", "restricted_zone_intrusion", "CAM", "R", ["track:1"], 0, 1, 2, 2, 0.9, {}, {"snapshot_raw": None, "snapshot_annotated": None, "clip": None, "metadata": None}, "cached_ai")
            manual = root / "manual.json"
            manual.write_text(json.dumps([incident.to_dict()]), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "manual_demo"):
                run_pipeline(parse_runtime_config({"execution_mode": "manual_demo"}), self.camera, self.rules, output_root=root / "out", manual_path=manual)


if __name__ == "__main__":
    unittest.main()
