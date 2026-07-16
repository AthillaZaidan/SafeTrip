import unittest

from transitshield_vision.detector import UltralyticsPersonDetector
from transitshield_vision.tracker import UltralyticsByteTracker
from transitshield_vision.video_io import iter_video_frames


class Values(list):
    def tolist(self):
        return list(self)

    def cpu(self):
        return self


class FakeBoxes:
    def __init__(self, *, ids=None):
        self.xyxy = Values([[1, 2, 11, 22]])
        self.conf = Values([0.8])
        self.cls = Values([0])
        self.id = None if ids is None else Values(ids)


class FakeResult:
    def __init__(self, *, ids=None):
        self.boxes = FakeBoxes(ids=ids)


class FakeModel:
    def __init__(self):
        self.predict_calls = []
        self.track_calls = []
        self.predictor = object()

    def predict(self, **kwargs):
        self.predict_calls.append(kwargs)
        return [FakeResult()]

    def track(self, **kwargs):
        self.track_calls.append(kwargs)
        return [FakeResult(ids=[7])]


class FakeCapture:
    def __init__(self, frames, fps=10):
        self.frames = iter(frames)
        self.fps = fps
        self.released = False

    def isOpened(self):
        return True

    def get(self, prop):
        return self.fps if prop == 5 else 3

    def read(self):
        try:
            return True, next(self.frames)
        except StopIteration:
            return False, None

    def release(self):
        self.released = True


class BackboneTests(unittest.TestCase):
    def test_video_reader_preserves_original_timestamps_with_stride(self):
        capture = FakeCapture(["f0", "f1", "f2"])
        frames = list(iter_video_frames("unused.mp4", frame_stride=2, capture_factory=lambda _: capture))
        self.assertEqual([(item.frame_index, item.timestamp_seconds, item.raw_bgr_frame) for item in frames], [(0, 0.0, "f0"), (2, 0.2, "f2")])
        self.assertTrue(capture.released)

    def test_detector_returns_typed_person_detection(self):
        model = FakeModel()
        detector = UltralyticsPersonDetector("unused.pt", model=model, confidence_threshold=0.35)
        detections = detector.detect("frame", frame_index=4, timestamp_seconds=0.4)
        self.assertEqual(detections[0].bbox_xyxy, (1.0, 2.0, 11.0, 22.0))
        self.assertEqual(model.predict_calls[0]["classes"], [0])

    def test_tracker_returns_track_observation_and_can_reset(self):
        model = FakeModel()
        tracker = UltralyticsByteTracker("unused.pt", model=model, image_size=1280)
        tracks = tracker.track("frame", frame_index=5, timestamp_seconds=0.5)
        self.assertEqual(tracks[0].track_id, 7)
        self.assertEqual(tracks[0].footpoint_xy, (6.0, 22.0))
        self.assertEqual(model.track_calls[0]["tracker"], "bytetrack.yaml")
        self.assertEqual(model.track_calls[0]["imgsz"], 1280)
        tracker.reset()
        self.assertIsNone(model.predictor)


if __name__ == "__main__":
    unittest.main()
