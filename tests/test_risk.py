import unittest

from transitshield_vision.risk_indicators import score_indicators


class RiskIndicatorTests(unittest.TestCase):
    def test_score_is_deterministic_and_lists_contributions(self):
        result = score_indicators(
            "person_running_on_track",
            {"inside_track_area": True, "normalized_speed": 1.2, "running_duration_seconds": 1.0},
        )
        self.assertEqual(result.score, 80)
        self.assertEqual(result.severity, "Critical")
        self.assertEqual(sum(item.points for item in result.contributions), result.score)

    def test_detection_confidence_is_not_a_risk_input(self):
        first = score_indicators("restricted_zone_intrusion", {"inside_restricted_zone": True, "restricted_dwell_seconds": 4, "detection_confidence": 0.1})
        second = score_indicators("restricted_zone_intrusion", {"inside_restricted_zone": True, "restricted_dwell_seconds": 4, "detection_confidence": 0.99})
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
