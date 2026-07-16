import tempfile
import unittest
from pathlib import Path

from transitshield_vision.config import parse_camera_config, parse_event_rules
from transitshield_vision.fallback import load_cached_frames, select_execution_source
from transitshield_vision.pipeline import SafetyPipeline


def track(track_id, x, y, width=4, height=10, confidence=0.9):
    return {
        "track_id": track_id,
        "confidence": confidence,
        "bbox_xyxy": [x - width / 2, y - height, x + width / 2, y],
    }


def pose_track(track_id, x, y, width=14, height=10, confidence=0.9, horizontal_score=0.8):
    return {
        **track(track_id, x, y, width, height, confidence),
        "horizontal_score": horizontal_score,
    }


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.camera = parse_camera_config(
            {
                "camera_id": "CAM",
                "video_path": "demo.mp4",
                "zones": [
                    {"zone_id": "RESTRICTED", "zone_type": "restricted", "polygon": [[0, 0], [10, 0], [10, 20], [0, 20]], "danger_direction": [1, 0]},
                    {"zone_id": "CROWD", "zone_type": "crowd_monitoring", "polygon": [[100, 0], [150, 0], [150, 20], [100, 20]], "capacity": 2},
                    {"zone_id": "NORMAL", "zone_type": "normal", "polygon": [[180, 0], [250, 0], [250, 20], [180, 20]]},
                ],
            },
            require_video=False,
        )
        self.rules = parse_event_rules(
            {
                "restricted_zone_intrusion": {"minimum_duration_seconds": 1, "cooldown_seconds": 5, "danger_direction_cosine_threshold": 0.5},
                "possible_person_down": {"minimum_duration_seconds": 1, "cooldown_seconds": 5, "minimum_aspect_ratio": 1.1, "maximum_normalized_speed": 0.08, "minimum_pose_horizontal_score": 0.65},
                "crowd_compression": {"minimum_duration_seconds": 1, "cooldown_seconds": 5, "minimum_density_ratio": 0.85, "minimum_density_growth": 0.4, "maximum_average_normalized_speed": 0.12, "density_growth_window_seconds": 2},
            }
        )

    def test_cached_tracks_produce_three_explainable_incidents(self):
        frames = [
            {"frame_index": 0, "timestamp_seconds": 0.0, "tracks": [track(1, 5, 10), track(2, 25, 10), track(3, 210, 10, 14, 10), track(10, 110, 10)]},
            {"frame_index": 1, "timestamp_seconds": 1.0, "tracks": [track(1, 5, 10), track(2, 35, 10), track(3, 210, 10, 14, 10), track(10, 110, 10)]},
            {"frame_index": 2, "timestamp_seconds": 2.0, "tracks": [track(1, 5, 10), track(2, 45, 10), track(3, 210, 10, 14, 10), track(10, 110, 10), track(11, 120, 10)]},
            {"frame_index": 3, "timestamp_seconds": 3.0, "tracks": [track(1, 5, 10), track(2, 55, 10), track(3, 210, 10, 14, 10), track(10, 110, 10), track(11, 120, 10)]},
        ]
        incidents = SafetyPipeline(self.camera, self.rules, source_mode="cached_ai").process_cached_frames(frames)
        self.assertEqual({incident.incident_type for incident in incidents}, {"restricted_zone_intrusion", "possible_person_down", "crowd_compression"})
        self.assertEqual(len({incident.incident_id for incident in incidents}), 3)

    def test_crowd_growth_does_not_use_stale_video_start_baseline(self):
        frames = [
            {"frame_index": 0, "timestamp_seconds": 0.0, "tracks": [track(10, 110, 10)]},
            {"frame_index": 10, "timestamp_seconds": 10.0, "tracks": [track(10, 110, 10), track(11, 120, 10)]},
            {"frame_index": 11, "timestamp_seconds": 11.0, "tracks": [track(10, 110, 10), track(11, 120, 10)]},
        ]
        incidents = SafetyPipeline(self.camera, self.rules, source_mode="cached_ai").process_cached_frames(frames)
        self.assertNotIn("crowd_compression", {incident.incident_type for incident in incidents})

    def test_crowd_motion_uses_median_to_ignore_one_moving_outlier(self):
        frames = [
            {"frame_index": 0, "timestamp_seconds": 0.0, "tracks": [track(10, 110, 10)]},
            {"frame_index": 2, "timestamp_seconds": 2.0, "tracks": [track(10, 110, 10), track(11, 120, 10), track(12, 130, 10)]},
            {"frame_index": 3, "timestamp_seconds": 3.0, "tracks": [track(10, 110, 10), track(11, 120, 10), track(12, 140, 10)]},
        ]

        incidents = SafetyPipeline(self.camera, self.rules, source_mode="cached_ai").process_cached_frames(frames)

        self.assertIn("crowd_compression", {incident.incident_type for incident in incidents})

    def test_pose_track_detects_person_who_falls_then_remains_down(self):
        frames = [
            {"frame_index": 0, "timestamp_seconds": 0.0, "tracks": [], "pose_tracks": [pose_track(7, 210, 10, width=4, horizontal_score=0.1)]},
            {"frame_index": 1, "timestamp_seconds": 1.0, "tracks": [], "pose_tracks": [pose_track(7, 210, 10)]},
            {"frame_index": 2, "timestamp_seconds": 2.0, "tracks": [], "pose_tracks": [pose_track(7, 210, 10)]},
        ]

        incidents = SafetyPipeline(self.camera, self.rules, source_mode="cached_ai").process_cached_frames(frames)

        self.assertEqual([incident.incident_type for incident in incidents], ["possible_person_down"])
        self.assertEqual(incidents[0].entity_ids, ["pose_track:7"])
        self.assertEqual(incidents[0].zone_id, "NORMAL")

    def test_switching_to_pose_mode_closes_regular_person_down_incident(self):
        frames = [
            {"frame_index": 0, "timestamp_seconds": 0.0, "tracks": [track(7, 210, 10, width=14)]},
            {"frame_index": 1, "timestamp_seconds": 1.0, "tracks": [track(7, 210, 10, width=14)]},
            {
                "frame_index": 2,
                "timestamp_seconds": 2.0,
                "tracks": [track(7, 210, 10, width=14)],
                "pose_tracks": [pose_track(70, 210, 10, width=4, horizontal_score=0.1)],
            },
        ]

        incidents = SafetyPipeline(self.camera, self.rules, source_mode="cached_ai").process_cached_frames(frames)
        incident = next(item for item in incidents if item.entity_ids == ["track:7"])

        self.assertEqual(incident.timestamp_end_seconds, 2.0)
        self.assertEqual(incident.duration_seconds, 2.0)

    def test_pose_track_detects_person_already_down_on_first_frame(self):
        frames = [
            {"frame_index": 0, "timestamp_seconds": 0.0, "tracks": [], "pose_tracks": [pose_track(8, 210, 10)]},
            {"frame_index": 1, "timestamp_seconds": 1.0, "tracks": [], "pose_tracks": [pose_track(8, 210, 10)]},
        ]

        incidents = SafetyPipeline(self.camera, self.rules, source_mode="cached_ai").process_cached_frames(frames)

        self.assertEqual([incident.incident_type for incident in incidents], ["possible_person_down"])

    def test_pose_track_tolerates_stationary_bbox_jitter(self):
        frames = [
            {
                "frame_index": index,
                "timestamp_seconds": index * 0.25,
                "tracks": [],
                "pose_tracks": [pose_track(9, (210, 211, 209)[index % 3], 10)],
            }
            for index in range(8)
        ]

        incidents = SafetyPipeline(self.camera, self.rules, source_mode="cached_ai").process_cached_frames(frames)

        self.assertEqual([incident.incident_type for incident in incidents], ["possible_person_down"])

    def test_cached_loader_rejects_missing_file_and_mode_never_falls_back(self):
        with self.assertRaises(FileNotFoundError):
            load_cached_frames("missing.jsonl")
        with self.assertRaisesRegex(ValueError, "execution_mode"):
            select_execution_source("automatic")
        self.assertEqual(select_execution_source("full_ai"), "full_ai")

    def test_cached_loader_reads_jsonl(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "tracks.jsonl"
            path.write_text('{"frame_index": 0, "timestamp_seconds": 0, "tracks": []}\n', encoding="utf-8")
            self.assertEqual(load_cached_frames(path)[0]["frame_index"], 0)

    def test_incident_keeps_zero_start_and_closes_on_condition_exit(self):
        frames = [
            {"frame_index": 0, "timestamp_seconds": 0.0, "tracks": [track(1, 5, 10)]},
            {"frame_index": 1, "timestamp_seconds": 1.0, "tracks": [track(1, 5, 10)]},
            {"frame_index": 2, "timestamp_seconds": 2.0, "tracks": [track(1, 15, 10)]},
        ]

        incidents = SafetyPipeline(self.camera, self.rules, source_mode="cached_ai").process_cached_frames(frames)
        incident = next(item for item in incidents if item.incident_type == "restricted_zone_intrusion")

        self.assertEqual(incident.timestamp_start_seconds, 0.0)
        self.assertEqual(incident.timestamp_detected_seconds, 1.0)
        self.assertEqual(incident.timestamp_end_seconds, 2.0)
        self.assertEqual(incident.duration_seconds, 2.0)

    def test_long_detection_gap_does_not_confirm_old_candidate(self):
        frames = [
            {"frame_index": 0, "timestamp_seconds": 0.0, "tracks": [track(1, 5, 10)]},
            {"frame_index": 1, "timestamp_seconds": 1.0, "tracks": []},
            {"frame_index": 2, "timestamp_seconds": 2.0, "tracks": []},
            {"frame_index": 3, "timestamp_seconds": 3.0, "tracks": []},
            {"frame_index": 4, "timestamp_seconds": 4.0, "tracks": [track(1, 5, 10)]},
        ]

        incidents = SafetyPipeline(self.camera, self.rules, source_mode="cached_ai").process_cached_frames(frames)

        self.assertNotIn("restricted_zone_intrusion", {item.incident_type for item in incidents})


if __name__ == "__main__":
    unittest.main()
