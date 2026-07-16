import unittest

from transitshield_vision.schemas import Incident, TrackObservation, ZoneConfig
from transitshield_vision.visualization import AnnotatedVideoSink, annotate_frame


def incident(incident_id, event_type, *, entities=(), zone_id=None, detected=1.0, indicators=None):
    return Incident(
        incident_id,
        event_type,
        "CAM",
        zone_id,
        list(entities),
        0.0,
        detected,
        None,
        detected,
        0.9,
        indicators or {},
        {"snapshot_raw": None, "snapshot_annotated": None, "clip": None, "metadata": None},
        "full_ai",
    )


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

    def test_annotation_labels_all_people_and_four_event_reasons(self):
        class Frame:
            def copy(self):
                return self

        class CV2:
            FONT_HERSHEY_SIMPLEX = 0
            LINE_AA = 0
            rectangles = []
            texts = []

            @classmethod
            def polylines(cls, *_args, **_kwargs):
                pass

            @classmethod
            def rectangle(cls, *args, **_kwargs):
                cls.rectangles.append(args[3])

            @classmethod
            def circle(cls, *_args, **_kwargs):
                pass

            @classmethod
            def putText(cls, *args, **_kwargs):
                cls.texts.append(args[1])

        crowd_zone = ZoneConfig("CROWD", "CAM", "crowd_monitoring", ((0, 0), (10, 0), (10, 10), (0, 10)), capacity=18)
        tracks = [
            TrackObservation(0, 2, 1, 0.91, (1, 1, 5, 9), (3, 9), 4, 8),
            TrackObservation(0, 2, 2, 0.92, (20, 1, 25, 9), (22.5, 9), 5, 8),
            TrackObservation(0, 2, 3, 0.93, (40, 1, 45, 9), (42.5, 9), 5, 8),
        ]
        pose_tracks = [TrackObservation(0, 2, 7, 0.88, (60, 1, 72, 8), (66, 8), 12, 7)]
        incidents = [
            incident("I1", "restricted_zone_intrusion", entities=["track:2"], indicators={"restricted_dwell_seconds": 1.5}),
            incident("I2", "person_running_on_track", entities=["track:2"], indicators={"normalized_speed": 1.24}),
            incident("I3", "possible_person_down", entities=["pose_track:7"], indicators={"horizontal_body_score": 0.99, "low_motion_seconds": 3.0}),
            incident("I4", "crowd_compression", zone_id="CROWD", indicators={"people_count": 20, "configured_capacity": 18}),
        ]

        annotate_frame(Frame(), [crowd_zone], tracks, pose_tracks=pose_tracks, incidents=incidents, timestamp_seconds=2.0, cv2_module=CV2)

        labels = "\n".join(CV2.texts)
        self.assertEqual(len(CV2.rectangles), 4)
        self.assertIn((0, 255, 0), CV2.rectangles)
        self.assertIn((0, 165, 255), CV2.rectangles)
        self.assertIn((0, 0, 255), CV2.rectangles)
        self.assertIn("Person #3 | 0.93", labels)
        self.assertIn("RESTRICTED INTRUSION | dwell 1.5s", labels)
        self.assertIn("RUNNING ON TRACK | speed 1.24", labels)
        self.assertIn("POSSIBLE DOWN | pose 0.99 | still 3.0s", labels)
        self.assertIn("CROWD COMPRESSION | 20/18 people", labels)

    def test_annotation_does_not_show_alert_before_confirmation(self):
        class Frame:
            def copy(self):
                return self

        class CV2:
            FONT_HERSHEY_SIMPLEX = 0
            LINE_AA = 0
            colors = []
            texts = []

            @classmethod
            def polylines(cls, *_args, **_kwargs):
                pass

            @classmethod
            def rectangle(cls, *args, **_kwargs):
                cls.colors.append(args[3])

            @classmethod
            def circle(cls, *_args, **_kwargs):
                pass

            @classmethod
            def putText(cls, *args, **_kwargs):
                cls.texts.append(args[1])

        track = TrackObservation(0, 1, 4, 0.9, (1, 1, 5, 9), (3, 9), 4, 8)
        alert = incident("I5", "restricted_zone_intrusion", entities=["track:4"], detected=2.0, indicators={"restricted_dwell_seconds": 1.5})

        annotate_frame(Frame(), [], [track], incidents=[alert], timestamp_seconds=1.0, cv2_module=CV2)

        self.assertEqual(CV2.colors, [(0, 255, 0)])
        self.assertNotIn("INTRUSION", "\n".join(CV2.texts))


if __name__ == "__main__":
    unittest.main()
