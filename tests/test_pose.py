import unittest

from transitshield_vision.pose import UltralyticsPoseEstimator, body_horizontal_score, match_pose_scores
from transitshield_vision.schemas import TrackObservation


class Values(list):
    def cpu(self):
        return self

    def tolist(self):
        return list(self)


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

    def test_pose_estimator_returns_persistent_track_id(self):
        keypoints = [[0, 0, 0] for _ in range(17)]
        keypoints[5] = [0, 0, 1]
        keypoints[6] = [2, 0, 1]
        keypoints[11] = [10, 1, 1]
        keypoints[12] = [12, 1, 1]

        class Model:
            predictor = object()
            calls = []

            def track(self, **kwargs):
                self.calls.append(kwargs)
                boxes = type("Boxes", (), {"xyxy": Values([[0, 0, 12, 5]]), "conf": Values([0.9]), "id": Values([7])})()
                result = type("Result", (), {"boxes": boxes, "keypoints": type("Keypoints", (), {"data": Values([keypoints])})()})()
                return [result]

        model = Model()
        estimator = UltralyticsPoseEstimator("unused.pt", model=model)
        poses = estimator.estimate("frame")

        self.assertEqual(poses[0].track_id, 7)
        self.assertTrue(model.calls[0]["persist"])
        self.assertEqual(model.calls[0]["tracker"], "bytetrack.yaml")
        estimator.reset()
        self.assertIsNone(model.predictor)


if __name__ == "__main__":
    unittest.main()
