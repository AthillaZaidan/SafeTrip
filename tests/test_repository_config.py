import unittest
from pathlib import Path

from transitshield_vision.config import load_json, parse_camera_config, parse_event_rules, parse_runtime_config


class RepositoryConfigTests(unittest.TestCase):
    def test_checked_in_configs_are_valid_and_enable_three_events(self):
        root = Path(__file__).parents[1]
        runtime = parse_runtime_config(load_json(root / "configs/runtime.json"))
        camera = parse_camera_config(load_json(root / "configs/cameras/demo_camera.json"), require_video=False)
        rules = parse_event_rules(load_json(root / "configs/event_rules.json"))
        self.assertEqual(runtime.execution_mode, "full_ai")
        self.assertEqual(camera.enabled_events, ("restricted_zone_intrusion",))
        self.assertEqual(len(rules), 3)
        self.assertEqual(rules["crowd_compression"]["minimum_duration_seconds"], 1.0)
        self.assertEqual(runtime.detector_image_size, 1280)
        self.assertEqual(runtime.person_confidence_threshold, 0.15)


if __name__ == "__main__":
    unittest.main()
