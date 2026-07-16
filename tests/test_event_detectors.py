import unittest

from transitshield_vision.event_detectors.crowd_compression import CrowdCompressionDetector
from transitshield_vision.event_detectors.person_down import PersonDownDetector
from transitshield_vision.event_detectors.restricted_intrusion import RestrictedIntrusionDetector
from transitshield_vision.event_detectors.running_on_track import RunningOnTrackDetector


class EventDetectorTests(unittest.TestCase):
    def test_restricted_intrusion_requires_persistence_and_emits_once(self):
        detector = RestrictedIntrusionDetector(minimum_duration_seconds=1.0, cooldown_seconds=5)
        self.assertIsNone(detector.update("CAM", "ZONE", 7, 0.0, True, 0.8, 0.9))
        event = detector.update("CAM", "ZONE", 7, 1.0, True, 0.8, 0.9)
        self.assertEqual(event.event_type, "restricted_zone_intrusion")
        self.assertIsNone(detector.update("CAM", "ZONE", 7, 1.1, True, 0.8, 0.9))

    def test_running_on_track_rejects_spike_and_confirms_sustained_speed(self):
        detector = RunningOnTrackDetector(minimum_normalized_speed=0.9, minimum_duration_seconds=0.5, cooldown_seconds=5)
        self.assertIsNone(detector.update("CAM", "TRACK", 2, 0.0, True, 1.2, 0.9))
        self.assertIsNone(detector.update("CAM", "TRACK", 2, 0.2, True, 0.2, 0.9))
        self.assertIsNone(detector.update("CAM", "TRACK", 2, 1.0, True, 1.0, 0.9))
        event = detector.update("CAM", "TRACK", 2, 1.5, True, 1.1, 0.9)
        self.assertEqual(event.event_type, "person_running_on_track")

    def test_person_down_requires_horizontal_low_motion_pattern(self):
        detector = PersonDownDetector(1.1, 0.08, 1.0, 5)
        self.assertIsNone(detector.update("CAM", 3, 0.0, 1.3, 0.04, 0.8, 0.9))
        event = detector.update("CAM", 3, 1.0, 1.3, 0.04, 0.8, 0.9)
        self.assertEqual(event.event_type, "possible_person_down")
        detector.update("CAM", 3, 2.0, 0.6, 0.01, 0.2, 0.9)

    def test_crowd_requires_density_growth_and_low_speed(self):
        detector = CrowdCompressionDetector(0.85, 0.15, 0.12, 1.0, 5)
        self.assertIsNone(detector.update("CAM", "CROWD", 0.0, 18, 20, 0.2, 0.08, 0.4))
        event = detector.update("CAM", "CROWD", 1.0, 19, 20, 0.2, 0.08, 0.4)
        self.assertEqual(event.event_type, "crowd_compression")


if __name__ == "__main__":
    unittest.main()
