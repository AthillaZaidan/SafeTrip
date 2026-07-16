import unittest

from transitshield_vision.config import parse_camera_config, parse_event_rules, parse_runtime_config


class ConfigTests(unittest.TestCase):
    def test_runtime_rejects_unknown_mode(self):
        with self.assertRaisesRegex(ValueError, "execution_mode"):
            parse_runtime_config({"execution_mode": "automatic_fallback"})

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

    def test_track_area_and_four_event_rules_are_supported(self):
        camera = parse_camera_config(
            {
                "camera_id": "CAM1",
                "video_path": "demo.mp4",
                "zones": [
                    {
                        "zone_id": "TRACK",
                        "zone_type": "track_area",
                        "polygon": [[0, 0], [10, 0], [10, 10], [0, 10]],
                    }
                ],
            },
            require_video=False,
        )
        rules = parse_event_rules(
            {
                "restricted_zone_intrusion": {"minimum_duration_seconds": 1.5, "cooldown_seconds": 10},
                "person_running_on_track": {"minimum_duration_seconds": 0.5, "cooldown_seconds": 10, "minimum_normalized_speed": 0.9},
                "possible_person_down": {"minimum_duration_seconds": 3, "cooldown_seconds": 15, "minimum_aspect_ratio": 1.1, "maximum_normalized_speed": 0.08},
                "crowd_compression": {"minimum_duration_seconds": 3, "cooldown_seconds": 20, "minimum_density_ratio": 0.85, "minimum_density_growth": 0.15, "maximum_average_normalized_speed": 0.12},
            }
        )
        self.assertEqual(camera.zones[0].zone_type, "track_area")
        self.assertEqual(set(rules), {"restricted_zone_intrusion", "person_running_on_track", "possible_person_down", "crowd_compression"})


if __name__ == "__main__":
    unittest.main()
