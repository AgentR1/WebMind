"""Code-only regression tests for cross-platform mouse behavior."""

import importlib.util
from pathlib import Path
import sys
import unittest
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "webuse_mouse_control.py"
SPEC = importlib.util.spec_from_file_location("webuse_mouse_control_test", SCRIPT)
mouse = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = mouse
SPEC.loader.exec_module(mouse)


class FakePyAutoGUI:
    FAILSAFE = True

    def __init__(self):
        self.released = False

    def mouseDown(self, button):
        self.button = button

    def mouseUp(self, button):
        self.released = button == "left"


class MouseTests(unittest.TestCase):
    def test_negative_coordinates_are_valid_inside_virtual_desktop(self):
        screen = mouse.Screen(left=-1920, top=-200, width=3840, height=1280)
        mouse.validate_coordinate(screen, -100, -100)
        with self.assertRaisesRegex(ValueError, "out of bounds"):
            mouse.validate_coordinate(screen, -1921, 0)

    def test_left_hold_releases_button_when_wait_is_interrupted(self):
        fake = FakePyAutoGUI()
        args = mouse.build_parser().parse_args(["left-hold", "--seconds", "1"])
        screen = mouse.Screen(left=0, top=0, width=100, height=100)
        point = mouse.Point(10, 10)
        with patch.object(mouse, "load_pyautogui", return_value=fake), \
             patch.object(mouse, "get_screen_and_position", return_value=(screen, point)), \
             patch.object(mouse.time, "sleep", side_effect=KeyboardInterrupt), \
             self.assertRaises(KeyboardInterrupt):
            mouse.run(args)
        self.assertTrue(fake.released)

    def test_negative_duration_is_rejected_by_parser(self):
        with self.assertRaises(SystemExit):
            mouse.build_parser().parse_args(["move-to", "--x", "1", "--y", "1", "--duration", "-1"])


if __name__ == "__main__":
    unittest.main()
