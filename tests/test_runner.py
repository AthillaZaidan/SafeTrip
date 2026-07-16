import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from transitshield_vision.config import parse_camera_config, parse_event_rules, parse_runtime_config
from transitshield_vision.runner import run_pipeline
from transitshield_vision.schemas import Incident, TrackObservation
from transitshield_vision.video_io import VideoFrame


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
            self.assertTrue(result.incidents[0].evidence["metadata"].startswith((root / "out" / "incidents").as_posix()))
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

    def test_full_ai_cache_contains_pose_score_from_optional_pose_model(self):
        class Tracker:
            def track(self, _frame, *, frame_index, timestamp_seconds):
                return [TrackObservation(frame_index, timestamp_seconds, 1, 0.9, (0, 0, 10, 5), (5, 5), 10, 5)]

            def reset(self):
                pass

        class Pose:
            def estimate(self, _frame):
                return [type("PoseResult", (), {"bbox_xyxy": (0, 0, 10, 5), "horizontal_score": 0.8})()]

        with tempfile.TemporaryDirectory() as directory, patch(
            "transitshield_vision.runner.iter_video_frames",
            return_value=iter([VideoFrame(0, 0.0, 25.0, "frame")]),
        ):
            output = Path(directory) / "out"
            run_pipeline(
                parse_runtime_config({"execution_mode": "full_ai", "save_annotated_video": False}),
                self.camera,
                self.rules,
                output_root=output,
                tracker=Tracker(),
                pose_estimator=Pose(),
            )
            cache = json.loads((output / "frame-events/unused_tracks.jsonl").read_text(encoding="utf-8"))
            self.assertEqual(cache["pose_scores"], {"1": 0.8})

    def test_full_ai_invokes_evidence_generator_for_confirmed_incident(self):
        class Tracker:
            def track(self, _frame, *, frame_index, timestamp_seconds):
                return [TrackObservation(frame_index, timestamp_seconds, 1, 0.9, (0, 0, 10, 5), (5, 5), 10, 5)]

            def reset(self):
                pass

        rules = {event: values.copy() for event, values in self.rules.items()}
        rules["possible_person_down"]["minimum_duration_seconds"] = 0
        calls = []
        with tempfile.TemporaryDirectory() as directory, patch(
            "transitshield_vision.runner.iter_video_frames",
            return_value=iter([VideoFrame(0, 0.0, 25.0, "frame")]),
        ):
            result = run_pipeline(
                parse_runtime_config({"execution_mode": "full_ai", "save_annotated_video": False, "pose_weights": None}),
                self.camera,
                rules,
                output_root=Path(directory) / "out",
                tracker=Tracker(),
                evidence_generator=lambda camera, incident, frames, root: calls.append((camera.camera_id, incident.incident_id, root)),
            )
            self.assertEqual(len(result.incidents), 1)
            self.assertEqual(len(calls), 1)

    def test_full_ai_resets_tracker_when_frame_processing_fails(self):
        class Tracker:
            reset_called = False

            def track(self, *_args, **_kwargs):
                raise RuntimeError("tracking failed")

            def reset(self):
                self.reset_called = True

        tracker = Tracker()
        with tempfile.TemporaryDirectory() as directory, patch(
            "transitshield_vision.runner.iter_video_frames",
            return_value=iter([VideoFrame(0, 0.0, 25.0, "frame")]),
        ):
            with self.assertRaisesRegex(RuntimeError, "tracking failed"):
                run_pipeline(
                    parse_runtime_config({"execution_mode": "full_ai", "save_annotated_video": False, "pose_weights": None}),
                    self.camera,
                    self.rules,
                    output_root=Path(directory) / "out",
                    tracker=tracker,
                )
        self.assertTrue(tracker.reset_called)


if __name__ == "__main__":
    unittest.main()
