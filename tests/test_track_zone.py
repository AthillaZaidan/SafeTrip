import unittest

from transitshield_vision.schemas import TrackObservation, ZoneConfig
from transitshield_vision.track_state import TrackStateManager
from transitshield_vision.zone_analysis import get_active_zone, validate_zones_for_frame


def observation(frame, timestamp, x, y=10, width=4, height=10):
    return TrackObservation(frame, timestamp, 1, 0.9, (x - width / 2, y - height, x + width / 2, y), (x, y), width, height)


class TrackAndZoneTests(unittest.TestCase):
    def test_track_state_uses_elapsed_time_and_resets_after_gap(self):
        manager = TrackStateManager(history_size=4, missing_frame_tolerance=1)
        manager.update(observation(0, 0.0, 0))
        state = manager.update(observation(1, 1.0, 10))
        self.assertAlmostEqual(state.normalized_speed, 1.0)
        self.assertEqual(state.direction_vector, (1.0, 0.0))
        state = manager.update(observation(4, 4.0, 20))
        self.assertEqual(state.normalized_speed, 0.0)

    def test_active_zone_uses_footpoint_and_first_configured_match(self):
        restricted = ZoneConfig("R", "CAM", "restricted", ((0, 0), (10, 0), (10, 10), (0, 10)))
        normal = ZoneConfig("N", "CAM", "normal", ((0, 0), (20, 0), (20, 20), (0, 20)))
        self.assertEqual(get_active_zone((5, 5), (restricted, normal)).zone_id, "R")
        self.assertIsNone(get_active_zone((30, 30), (restricted, normal)))

    def test_zone_coordinates_must_fit_frame(self):
        invalid = ZoneConfig("R", "CAM", "restricted", ((0, 0), (101, 0), (10, 10)))
        with self.assertRaisesRegex(ValueError, "outside frame"):
            validate_zones_for_frame((invalid,), width=100, height=100)


if __name__ == "__main__":
    unittest.main()
