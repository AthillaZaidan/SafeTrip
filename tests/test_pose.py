import unittest

from transitshield_vision.pose import body_horizontal_score, match_pose_scores
from transitshield_vision.schemas import TrackObservation


class PoseTests(unittest.TestCase):
    def test_body_axis_horizontal_score_uses_shoulders_and_hips(self):
        keypoints = [(0, 0, 0)] * 17
        keypoints[5] = (0, 0, 1)
        keypoints[6] = (2, 0, 1)
        keypoints[11] = (10, 1, 1)
        keypoints[12] = (12, 1, 1)
        self.assertGreater(body_horizontal_score(keypoints), 0.99)

    def test_pose_box_is_matched_to_track_by_iou(self):
        track = TrackObservation(0, 0, 4, 0.9, (0, 0, 10, 10), (5, 10), 10, 10)
        scores = match_pose_scores([track], [((1, 1, 9, 9), 0.8)])
        self.assertEqual(scores, {4: 0.8})


if __name__ == "__main__":
    unittest.main()
