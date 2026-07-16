import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from transitshield_vision.config import parse_camera_config, parse_event_rules, parse_runtime_config
from transitshield_vision.runner import RunResult, _render_annotated_video, run_pipeline, write_library_result
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
            self.assertTrue(Path(result.incidents[0].evidence["metadata"]).is_file())
            self.assertIsNone(result.incidents[0].evidence["clip"])
            self.assertTrue((root / "out" / "incidents.json").is_file())
            self.assertTrue((root / "out" / "pipeline_summary.json").is_file())

    def test_manual_mode_rejects_missing_prepared_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            incident = Incident("INC_CAM_1", "restricted_zone_intrusion", "CAM", "R", ["track:1"], 0, 1, 2, 2, 0.9, {}, {"snapshot_raw": None, "snapshot_annotated": None, "clip": "missing.mp4", "metadata": None}, "manual_demo")
            manual = root / "manual.json"
            manual.write_text(json.dumps([incident.to_dict()]), encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "evidence file does not exist"):
                run_pipeline(parse_runtime_config({"execution_mode": "manual_demo"}), self.camera, self.rules, output_root=root / "out", manual_path=manual)

    def test_manual_mode_requires_explicit_manual_source_mode(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            incident = Incident("INC_CAM_1", "restricted_zone_intrusion", "CAM", "R", ["track:1"], 0, 1, 2, 2, 0.9, {}, {"snapshot_raw": None, "snapshot_annotated": None, "clip": None, "metadata": None}, "cached_ai")
            manual = root / "manual.json"
            manual.write_text(json.dumps([incident.to_dict()]), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "manual_demo"):
                run_pipeline(parse_runtime_config({"execution_mode": "manual_demo"}), self.camera, self.rules, output_root=root / "out", manual_path=manual)

    def test_full_ai_cache_contains_tracks_from_optional_pose_model(self):
        class Tracker:
            def track(self, _frame, *, frame_index, timestamp_seconds):
                return [TrackObservation(frame_index, timestamp_seconds, 1, 0.9, (0, 0, 10, 5), (5, 5), 10, 5)]

            def reset(self):
                pass

        class Pose:
            reset_called = False

            def estimate(self, _frame):
                return [type("PoseResult", (), {"track_id": 7, "bbox_xyxy": (0, 0, 10, 5), "confidence": 0.85, "horizontal_score": 0.8})()]

            def reset(self):
                self.reset_called = True

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
            self.assertEqual(cache["pose_tracks"], [{"track_id": 7, "confidence": 0.85, "bbox_xyxy": [0, 0, 10, 5], "horizontal_score": 0.8}])

    def test_pose_failure_falls_back_to_regular_tracks(self):
        class Tracker:
            def track(self, _frame, *, frame_index, timestamp_seconds):
                return [TrackObservation(frame_index, timestamp_seconds, 1, 0.9, (0, 0, 10, 5), (5, 5), 10, 5)]

            def reset(self):
                pass

        class Pose:
            def estimate(self, _frame):
                raise RuntimeError("pose unavailable")

            def reset(self):
                pass

        rules = {event: values.copy() for event, values in self.rules.items()}
        rules["possible_person_down"]["minimum_duration_seconds"] = 1
        camera = parse_camera_config(
            {
                "camera_id": "DOWN_CAM",
                "video_path": "unused.mp4",
                "enabled_events": ["possible_person_down"],
                "zones": [{"zone_id": "PLATFORM", "zone_type": "normal", "polygon": [[0, 0], [20, 0], [20, 20], [0, 20]]}],
            },
            require_video=False,
        )
        frames = [VideoFrame(0, 0.0, 25.0, "frame"), VideoFrame(1, 1.0, 25.0, "frame")]
        with tempfile.TemporaryDirectory() as directory, patch("transitshield_vision.runner.iter_video_frames", return_value=iter(frames)):
            result = run_pipeline(
                parse_runtime_config({"execution_mode": "full_ai", "save_annotated_video": False}),
                camera,
                rules,
                output_root=Path(directory) / "out",
                tracker=Tracker(),
                pose_estimator=Pose(),
                evidence_generator=lambda *_args: None,
            )

        self.assertEqual([item.incident_type for item in result.incidents], ["possible_person_down"])
        self.assertIn("pose inference disabled at frame 0: pose unavailable", result.summary["warnings"])

    def test_successful_empty_pose_frame_keeps_pose_mode_explicit(self):
        class Tracker:
            def track(self, *_args, **_kwargs):
                return []

            def reset(self):
                pass

        class Pose:
            def estimate(self, _frame):
                return []

            def reset(self):
                pass

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
            cached = json.loads((output / "frame-events/unused_tracks.jsonl").read_text(encoding="utf-8"))

        self.assertIn("pose_tracks", cached)
        self.assertEqual(cached["pose_tracks"], [])

    def test_full_ai_validates_zones_against_real_frame_dimensions(self):
        class Frame:
            shape = (100, 100, 3)

        class Tracker:
            def track(self, *_args, **_kwargs):
                return []

            def reset(self):
                pass

        camera = parse_camera_config(
            {
                "camera_id": "CAM",
                "video_path": "unused.mp4",
                "enabled_events": ["restricted_zone_intrusion"],
                "zones": [{"zone_id": "R", "zone_type": "restricted", "polygon": [[0, 0], [101, 0], [0, 10]]}],
            },
            require_video=False,
        )
        with tempfile.TemporaryDirectory() as directory, patch(
            "transitshield_vision.runner.iter_video_frames",
            return_value=iter([VideoFrame(0, 0.0, 25.0, Frame())]),
        ):
            with self.assertRaisesRegex(ValueError, "outside frame"):
                run_pipeline(
                    parse_runtime_config({"execution_mode": "full_ai", "save_annotated_video": False, "pose_weights": None}),
                    camera,
                    self.rules,
                    output_root=Path(directory) / "out",
                    tracker=Tracker(),
                )

    def test_summary_identifies_runtime_models_and_device(self):
        class Tracker:
            def track(self, *_args, **_kwargs):
                return []

            def reset(self):
                pass

        runtime = parse_runtime_config({"execution_mode": "full_ai", "device": "cpu", "detector_weights": "people.pt", "pose_weights": None, "save_annotated_video": False})
        with tempfile.TemporaryDirectory() as directory, patch(
            "transitshield_vision.runner.iter_video_frames",
            return_value=iter([VideoFrame(0, 0.0, 25.0, "frame")]),
        ):
            result = run_pipeline(runtime, self.camera, self.rules, output_root=Path(directory) / "out", tracker=Tracker())

        self.assertEqual(result.summary["models"], {"detector_weights": "people.pt", "pose_weights": None, "device": "cpu"})

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

    def test_full_ai_honors_custom_cache_path(self):
        class Tracker:
            def track(self, *_args, **_kwargs):
                return []

            def reset(self):
                pass

        with tempfile.TemporaryDirectory() as directory, patch(
            "transitshield_vision.runner.iter_video_frames",
            return_value=iter([VideoFrame(0, 0.0, 25.0, "frame")]),
        ):
            root = Path(directory)
            cache = root / "custom" / "tracks.jsonl"
            result = run_pipeline(
                parse_runtime_config({"execution_mode": "full_ai", "save_annotated_video": False, "pose_weights": None}),
                self.camera,
                self.rules,
                output_root=root / "out",
                cache_path=cache,
                tracker=Tracker(),
            )

            self.assertTrue(cache.is_file())
            self.assertEqual(result.output_paths["track_cache"], cache.as_posix())

    def test_failed_annotated_render_is_not_reported_as_output(self):
        class Tracker:
            def track(self, *_args, **_kwargs):
                return []

            def reset(self):
                pass

        with tempfile.TemporaryDirectory() as directory, patch(
            "transitshield_vision.runner.iter_video_frames",
            return_value=iter([VideoFrame(0, 0.0, 25.0, "frame")]),
        ), patch("transitshield_vision.runner._render_annotated_video", side_effect=RuntimeError("writer failed")):
            result = run_pipeline(
                parse_runtime_config({"execution_mode": "full_ai", "save_annotated_video": True, "pose_weights": None}),
                self.camera,
                self.rules,
                output_root=Path(directory) / "out",
                tracker=Tracker(),
            )

        self.assertIsNone(result.output_paths["annotated_video"])
        self.assertIn("annotated video disabled: writer failed", result.summary["warnings"])

    def test_zero_frame_render_does_not_report_stale_annotated_video(self):
        class Tracker:
            def track(self, *_args, **_kwargs):
                return []

            def reset(self):
                pass

        with tempfile.TemporaryDirectory() as directory, patch(
            "transitshield_vision.runner.iter_video_frames",
            side_effect=[iter([VideoFrame(0, 0.0, 25.0, "frame")]), iter([])],
        ):
            output = Path(directory) / "out"
            stale = output / "annotated-videos/unused_annotated.mp4"
            stale.parent.mkdir(parents=True)
            stale.write_bytes(b"stale")
            result = run_pipeline(
                parse_runtime_config({"execution_mode": "full_ai", "save_annotated_video": True, "pose_weights": None}),
                self.camera,
                self.rules,
                output_root=output,
                tracker=Tracker(),
            )

        self.assertIsNone(result.output_paths["annotated_video"])

    def test_library_result_combines_camera_incidents(self):
        first = Incident("I1", "restricted_zone_intrusion", "CAM1", "R", ["track:1"], 0, 1, 2, 2, 0.9, {}, {"snapshot_raw": None, "snapshot_annotated": None, "clip": None, "metadata": None}, "cached_ai")
        second = Incident("I2", "crowd_compression", "CAM2", "C", ["CAM2:C"], 3, 4, 5, 2, 0.8, {}, {"snapshot_raw": None, "snapshot_annotated": None, "clip": None, "metadata": None}, "cached_ai")
        results = [
            RunResult((first,), {"camera_id": "CAM1"}, {}),
            RunResult((second,), {"camera_id": "CAM2"}, {}),
        ]

        with tempfile.TemporaryDirectory() as directory:
            paths = write_library_result(results, directory)
            incidents = json.loads(Path(paths["incidents"]).read_text(encoding="utf-8"))

        self.assertEqual([item["incident_id"] for item in incidents], ["I1", "I2"])

    def test_full_ai_resets_optional_pose_tracker(self):
        class Tracker:
            def track(self, *_args, **_kwargs):
                return []

            def reset(self):
                pass

        class Pose:
            reset_called = False

            def estimate(self, _frame):
                return []

            def reset(self):
                self.reset_called = True

        pose = Pose()
        with tempfile.TemporaryDirectory() as directory, patch(
            "transitshield_vision.runner.iter_video_frames",
            return_value=iter([VideoFrame(0, 0.0, 25.0, "frame")]),
        ):
            run_pipeline(
                parse_runtime_config({"execution_mode": "full_ai", "save_annotated_video": False}),
                self.camera,
                self.rules,
                output_root=Path(directory) / "out",
                tracker=Tracker(),
                pose_estimator=pose,
            )

        self.assertTrue(pose.reset_called)

    def test_full_ai_skips_pose_for_camera_without_person_down(self):
        class Tracker:
            def track(self, *_args, **_kwargs):
                return []

            def reset(self):
                pass

        class Pose:
            def estimate(self, _frame):
                raise AssertionError("pose must not run for a crowd-only camera")

            def reset(self):
                pass

        camera = parse_camera_config(
            {
                "camera_id": "CROWD_CAM",
                "video_path": "unused.mp4",
                "enabled_events": ["crowd_compression"],
                "zones": [{"zone_id": "C", "zone_type": "crowd_monitoring", "polygon": [[0, 0], [10, 0], [10, 10]], "capacity": 5}],
            },
            require_video=False,
        )
        with tempfile.TemporaryDirectory() as directory, patch(
            "transitshield_vision.runner.iter_video_frames",
            return_value=iter([VideoFrame(0, 0.0, 25.0, "frame")]),
        ):
            result = run_pipeline(
                parse_runtime_config({"execution_mode": "full_ai", "save_annotated_video": False}),
                camera,
                self.rules,
                output_root=Path(directory) / "out",
                tracker=Tracker(),
                pose_estimator=Pose(),
            )

        self.assertEqual(result.summary["incident_counts"], {"crowd_compression": 0})

    def test_full_ai_renders_video_after_incidents_are_confirmed(self):
        class Tracker:
            def track(self, _frame, *, frame_index, timestamp_seconds):
                return [TrackObservation(frame_index, timestamp_seconds, 1, 0.9, (0, 0, 10, 5), (5, 5), 10, 5)]

            def reset(self):
                pass

        class Sink:
            def __init__(self, *_args, **_kwargs):
                pass

            def write(self, _frame):
                pass

            def close(self):
                pass

        rules = {event: values.copy() for event, values in self.rules.items()}
        rules["possible_person_down"]["minimum_duration_seconds"] = 0
        annotation_calls = []

        def annotate(frame, _zones, _tracks, *_args, **kwargs):
            annotation_calls.append([incident.incident_type for incident in kwargs.get("incidents", [])])
            return frame

        video_frames = [VideoFrame(0, 0.0, 25.0, "frame")]
        with tempfile.TemporaryDirectory() as directory, patch(
            "transitshield_vision.runner.iter_video_frames",
            side_effect=[iter(video_frames), iter(video_frames)],
        ), patch("transitshield_vision.runner.AnnotatedVideoSink", Sink), patch(
            "transitshield_vision.runner.annotate_frame",
            side_effect=annotate,
        ):
            run_pipeline(
                parse_runtime_config({"execution_mode": "full_ai", "save_annotated_video": True, "pose_weights": None}),
                self.camera,
                rules,
                output_root=Path(directory) / "out",
                tracker=Tracker(),
                evidence_generator=lambda *_args: None,
            )

        self.assertEqual(annotation_calls, [["possible_person_down"]])

    def test_second_pass_holds_tracks_across_stride_and_stops_at_last_cached_frame(self):
        class Sink:
            def __init__(self, *_args, **_kwargs):
                pass

            def write(self, _frame):
                pass

            def close(self):
                pass

        cached_frames = [
            {"frame_index": 0, "timestamp_seconds": 0.0, "tracks": [{"track_id": 1, "confidence": 0.9, "bbox_xyxy": [0, 0, 4, 8]}]},
            {"frame_index": 2, "timestamp_seconds": 0.2, "tracks": [{"track_id": 2, "confidence": 0.8, "bbox_xyxy": [1, 0, 5, 8]}]},
        ]
        video_frames = [VideoFrame(index, index / 10, 10.0, "frame") for index in range(4)]
        rendered_track_ids = []

        def annotate(frame, _zones, tracks, *_args, **_kwargs):
            rendered_track_ids.append([track.track_id for track in tracks])
            return frame

        with patch("transitshield_vision.runner.iter_video_frames", return_value=iter(video_frames)), patch(
            "transitshield_vision.runner.AnnotatedVideoSink",
            Sink,
        ), patch("transitshield_vision.runner.annotate_frame", side_effect=annotate):
            _render_annotated_video(self.camera, cached_frames, [], Path("unused.mp4"))

        self.assertEqual(rendered_track_ids, [[1], [1], [2]])


if __name__ == "__main__":
    unittest.main()
