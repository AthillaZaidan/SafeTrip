import unittest

from transitshield_vision.config import parse_camera_config, parse_event_rules, parse_runtime_config


class ConfigTests(unittest.TestCase):
    def test_runtime_rejects_unknown_mode(self):
        with self.assertRaisesRegex(ValueError, "execution_mode"):
            parse_runtime_config({"execution_mode": "automatic_fallback"})

    def test_runtime_rejects_non_positive_detector_image_size(self):
        with self.assertRaisesRegex(ValueError, "detector_image_size"):
            parse_runtime_config({"detector_image_size": 0})

    def test_camera_rejects_invalid_polygon(self):
        with self.assertRaisesRegex(ValueError, "polygon"):
            parse_camera_config(
                {
                    "camera_id": "CAM1",
                    "video_path": "demo.mp4",
                    "zones": [{"zone_id": "Z1", "zone_type": "restricted", "polygon": [[0, 0], [1, 1]]}],
                },
                require_video=False,
            )

    def test_camera_selects_from_exactly_three_mvp_events(self):
        camera = parse_camera_config(
            {
                "camera_id": "CAM1",
                "video_path": "demo.mp4",
                "enabled_events": ["crowd_compression"],
                "zones": [
                    {
                        "zone_id": "CROWD",
                        "zone_type": "crowd_monitoring",
                        "polygon": [[0, 0], [10, 0], [10, 10], [0, 10]],
                        "capacity": 10,
                    }
                ],
            },
            require_video=False,
        )
        rules = parse_event_rules(
            {
                "restricted_zone_intrusion": {"minimum_duration_seconds": 1.5, "cooldown_seconds": 10},
                "possible_person_down": {"minimum_duration_seconds": 3, "cooldown_seconds": 15, "minimum_aspect_ratio": 1.1, "maximum_normalized_speed": 0.08},
                "crowd_compression": {"minimum_duration_seconds": 3, "cooldown_seconds": 20, "minimum_density_ratio": 0.85, "minimum_density_growth": 0.15, "maximum_average_normalized_speed": 0.12},
            }
        )
        self.assertEqual(camera.enabled_events, ("crowd_compression",))
        self.assertEqual(set(rules), {"restricted_zone_intrusion", "possible_person_down", "crowd_compression"})

    def test_camera_rejects_unknown_enabled_event(self):
        with self.assertRaisesRegex(ValueError, "enabled_events"):
            parse_camera_config(
                {
                    "camera_id": "CAM1",
                    "video_path": "demo.mp4",
                    "enabled_events": ["person_running_on_track"],
                    "zones": [{"zone_id": "R", "zone_type": "restricted", "polygon": [[0, 0], [10, 0], [10, 10]]}],
                },
                require_video=False,
            )


if __name__ == "__main__":
    unittest.main()
