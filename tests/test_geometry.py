import unittest

from transitshield_vision.geometry import (
    bbox_footpoint,
    direction_alignment,
    motion_features,
    point_in_polygon,
)


class GeometryTests(unittest.TestCase):
    def test_bbox_footpoint_uses_bottom_center(self):
        self.assertEqual(bbox_footpoint((10, 20, 30, 80)), (20.0, 80.0))

    def test_polygon_membership_includes_boundary_and_concavity(self):
        polygon = [(0, 0), (4, 0), (4, 4), (2, 2), (0, 4)]
        self.assertTrue(point_in_polygon((1, 1), polygon))
        self.assertTrue(point_in_polygon((2, 2), polygon))
        self.assertFalse(point_in_polygon((2, 3), polygon))

    def test_motion_is_per_second_and_height_normalized(self):
        features = motion_features((0, 0), (30, 40), 1.0, bbox_height=100)
        self.assertAlmostEqual(features.speed_pixels_per_second, 50.0)
        self.assertAlmostEqual(features.normalized_speed, 0.5)
        self.assertEqual(features.direction_vector, (0.6, 0.8))

    def test_direction_alignment_is_cosine(self):
        self.assertAlmostEqual(direction_alignment((1, 0), (1, 0)), 1.0)
        self.assertAlmostEqual(direction_alignment((1, 0), (0, 1)), 0.0)


if __name__ == "__main__":
    unittest.main()
