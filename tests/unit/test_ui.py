"""Tests for the presentation-only ADAS UI and its in-memory state."""

import unittest
from types import SimpleNamespace

import numpy as np

import config
from ui import ADASUI, SystemState


class SystemStateTests(unittest.TestCase):
    def setUp(self):
        self.state = SystemState("sample_videos/test2.mp4")
        self.track = SimpleNamespace(id=7)

    def test_safety_status_comes_from_existing_collision_results(self):
        self.state.update_frame([self.track], [], 18.0, 1)
        self.assertEqual(self.state.safety_status, "SAFE")

        self.state.update_frame(
            [self.track],
            [(self.track, config.COLLISION_GROWTH_RATE_THRESHOLD * 1.1)],
            18.0,
            2,
        )
        self.assertEqual(self.state.safety_status, "WARNING")

        self.state.update_frame(
            [self.track],
            [(
                self.track,
                config.COLLISION_GROWTH_RATE_THRESHOLD
                * config.UI_DANGER_RATE_MULTIPLIER,
            )],
            18.0,
            3,
        )
        self.assertEqual(self.state.safety_status, "DANGER")

    def test_partial_ocr_is_stored_exactly_without_guessing(self):
        crop = np.zeros((24, 80, 3), dtype=np.uint8)
        self.state.record_plate(7, "57579", 0.58, "UNCERTAIN", crop)
        self.assertEqual(self.state.last_plate, "57579")
        self.assertEqual(self.state.plate_history[0].text, "57579")
        self.assertEqual(self.state.plate_history[0].status, "UNCERTAIN")


class ADASUITests(unittest.TestCase):
    def test_all_tabs_render_without_running_ai(self):
        ui = ADASUI()
        state = SystemState(0)
        frame = np.zeros((360, 640, 3), dtype=np.uint8)
        result = {
            "vehicles": [
                {"id": 1, "class": "car", "box": (30, 40, 200, 180), "confidence": 0.9}
            ],
            "people": [],
            "plates": [],
            "warned_ids": set(),
        }
        rendered = ui.render_camera(frame.copy(), result, state)
        for tab in (ui.LIVE_TAB, ui.PLATES_TAB, ui.HISTORY_TAB):
            ui.active_tab = tab
            canvas = ui.compose(rendered, state)
            self.assertEqual(canvas.shape, (config.UI_HEIGHT, config.UI_WIDTH, 3))

    def test_keyboard_controls(self):
        ui = ADASUI()
        ui.handle_key(ord("2"))
        self.assertEqual(ui.active_tab, ui.PLATES_TAB)
        ui.handle_key(ord("3"))
        self.assertEqual(ui.active_tab, ui.HISTORY_TAB)
        ui.handle_key(ord("d"))
        self.assertTrue(ui.debug_mode)

    def test_all_rejected_plates_are_hidden_in_debug(self):
        ui = ADASUI(debug_mode=True)
        state = SystemState("video.mp4")
        frame = np.zeros((120, 240, 3), dtype=np.uint8)
        labels = []
        ui._draw_labeled_box = lambda frame, box, color, label=None, thickness=2: labels.append(label)
        ui.render_camera(
            frame,
            {
                "vehicles": [],
                "people": [],
                "warned_ids": set(),
                "plates": [
                    {
                        "accepted": False,
                        "reason": "LOW_CONFIDENCE",
                        "confidence": 0.2,
                        "box": (10, 10, 60, 30),
                    },
                    {
                        "accepted": False,
                        "reason": "OUTSIDE_VEHICLE",
                        "confidence": 0.8,
                        "box": (80, 10, 140, 30),
                    }
                ],
            },
            state,
        )
        self.assertEqual(labels, [])


if __name__ == "__main__":
    unittest.main()
