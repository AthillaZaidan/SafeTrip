import unittest

from transitshield_vision.event_state_machine import EventStateMachine


class EventStateMachineTests(unittest.TestCase):
    def test_confirms_once_then_suppresses_during_cooldown(self):
        machine = EventStateMachine(minimum_duration_seconds=1.0, cooldown_seconds=2.0)
        self.assertFalse(machine.update("entity", True, 0.0).confirmed_now)
        self.assertTrue(machine.update("entity", True, 1.0).confirmed_now)
        self.assertFalse(machine.update("entity", True, 1.2).confirmed_now)
        self.assertTrue(machine.update("entity", False, 1.5).closed_now)
        self.assertFalse(machine.update("entity", True, 2.0).confirmed_now)
        self.assertFalse(machine.update("entity", True, 3.6).confirmed_now)
        self.assertTrue(machine.update("entity", True, 4.6).confirmed_now)

    def test_gap_resets_candidate_duration(self):
        machine = EventStateMachine(minimum_duration_seconds=1.0, cooldown_seconds=0)
        machine.update("entity", True, 0.0)
        machine.update("entity", False, 0.5)
        self.assertFalse(machine.update("entity", True, 1.0).confirmed_now)
        self.assertTrue(machine.update("entity", True, 2.0).confirmed_now)


if __name__ == "__main__":
    unittest.main()
