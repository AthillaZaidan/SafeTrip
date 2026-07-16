import unittest

from transitshield_vision.schemas import TrackObservation, ZoneConfig
from transitshield_vision.visualization import AnnotatedVideoSink, annotate_frame


class VisualizationTests(unittest.TestCase):
    def test_annotation_draws_zone_track_footpoint_and_event_label(self):
        class Frame:
            def copy(self):
                return self

        class CV2:
            FONT_HERSHEY_SIMPLEX = 0
            LINE_AA = 0
            calls = []

            @classmethod
            def polylines(cls, *args, **kwargs):
                cls.calls.append("zone")

            @classmethod
            def rectangle(cls, *args, **kwargs):
                cls.calls.append("box")

            @classmethod
            def circle(cls, *args, **kwargs):
                cls.calls.append("footpoint")

            @classmethod
            def putText(cls, *args, **kwargs):
                cls.calls.append("text")

        zone = ZoneConfig("TRACK", "CAM", "track_area", ((0, 0), (10, 0), (10, 10), (0, 10)))
        track = TrackObservation(0, 0, 1, 0.9, (1, 1, 5, 9), (3, 9), 4, 8)
        annotate_frame(Frame(), [zone], [track], ["person_running_on_track"], cv2_module=CV2)
        self.assertIn("zone", CV2.calls)
        self.assertIn("box", CV2.calls)
        self.assertIn("footpoint", CV2.calls)
        self.assertGreaterEqual(CV2.calls.count("text"), 3)

    def test_annotated_video_sink_opens_once_and_releases(self):
        class Frame:
            shape = (10, 20, 3)

        class Writer:
            def __init__(self):
                self.frames = 0
                self.released = False

            def isOpened(self):
                return True

            def write(self, _frame):
                self.frames += 1

            def release(self):
                self.released = True

        writer = Writer()

        class CV2:
            @staticmethod
            def VideoWriter(*_args):
                return writer

            @staticmethod
            def VideoWriter_fourcc(*_args):
                return 0

        sink = AnnotatedVideoSink("annotated.mp4", fps=25, cv2_module=CV2)
        sink.write(Frame())
        sink.write(Frame())
        sink.close()
        self.assertEqual(writer.frames, 2)
        self.assertTrue(writer.released)


if __name__ == "__main__":
    unittest.main()
