import unittest
from pathlib import Path

from transitshield_vision.config import load_json, parse_camera_config, parse_event_rules, parse_runtime_config


class RepositoryConfigTests(unittest.TestCase):
    def test_checked_in_configs_are_valid_and_enable_four_events(self):
        root = Path(__file__).parents[1]
        runtime = parse_runtime_config(load_json(root / "configs/runtime.json"))
        camera = parse_camera_config(load_json(root / "configs/cameras/demo_camera.json"), require_video=False)
        rules = parse_event_rules(load_json(root / "configs/event_rules.json"))
        self.assertEqual(runtime.execution_mode, "full_ai")
        self.assertIn("track_area", {zone.zone_type for zone in camera.zones})
        self.assertEqual(len(rules), 4)


if __name__ == "__main__":
    unittest.main()
