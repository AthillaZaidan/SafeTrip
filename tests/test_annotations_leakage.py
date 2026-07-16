import tempfile
import unittest
from pathlib import Path

from transitshield_vision.annotations import validate_annotation_document


class AnnotationAndLeakageTests(unittest.TestCase):
    def test_annotation_rejects_unknown_event_and_invalid_range(self):
        base = {"video_id": "v", "camera_id": "CAM", "fps": 25, "events": []}
        with self.assertRaisesRegex(ValueError, "event_type"):
            validate_annotation_document({**base, "events": [{"event_type": "crime", "start_frame": 0, "end_frame": 1}]})
        with self.assertRaisesRegex(ValueError, "frame range"):
            validate_annotation_document({**base, "events": [{"event_type": "crowd_compression", "start_frame": 3, "end_frame": 2}]})

    def test_production_source_contains_no_forbidden_inference_terms(self):
        source_root = Path(__file__).parents[1] / "src" / "transitshield_vision"
        forbidden = ("center" + "=True", "b" + "fill(", "best_f1" + "_threshold", "or" + "acle", "test" + "_gt")
        violations = []
        for path in source_root.rglob("*.py"):
            text = path.read_text(encoding="utf-8")
            violations.extend(f"{path.name}:{term}" for term in forbidden if term in text)
        self.assertEqual(violations, [])


if __name__ == "__main__":
    unittest.main()
