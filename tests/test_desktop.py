"""Desktop CLI checks with fake GUI modules; never send real input or capture screens."""

import contextlib
import importlib.util
import io
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
SCRIPTS = {name: SCRIPT_DIR / f"webmind_{name}.py" for name in ("screenshot", "mouse", "typing")}


class DesktopCliTests(unittest.TestCase):
    def setUp(self):
        self.gui = mock.Mock()
        self.gui.FAILSAFE = True
        self.gui.KEYBOARD_KEYS = ["a", "b", "c", "ctrl", "shift", "command", "alt", "enter", "space", "escape", "win"]
        self.gui.size.return_value = (1920, 1080)
        self.gui.position.return_value = (400, 300)

    def load(self, name):
        spec = importlib.util.spec_from_file_location(f"desktop_test_{name}", SCRIPTS[name])
        module = importlib.util.module_from_spec(spec)
        with mock.patch.dict(sys.modules, {spec.name: module, "pyautogui": self.gui}):
            spec.loader.exec_module(module)
        return module

    def invoke(self, module, *args):
        stdout, stderr = io.StringIO(), io.StringIO()
        with mock.patch.dict(sys.modules, {"pyautogui": self.gui}):
            with mock.patch.object(sys, "argv", [str(module.__file__), *args, "--json"]):
                with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                    code = module.main()
        payload = json.loads(stdout.getvalue() or stderr.getvalue())
        return code, payload

    def assert_no_input(self):
        for name in ("moveTo", "moveRel", "scroll", "click", "mouseDown", "mouseUp", "write", "press", "keyDown", "keyUp", "hotkey"):
            getattr(self.gui, name).assert_not_called()

    def test_help_needs_no_optional_dependencies(self):
        for name, script in SCRIPTS.items():
            with self.subTest(name=name):
                result = subprocess.run([sys.executable, "-S", str(script), "--help"],
                                        capture_output=True, text=True, timeout=10)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("WebMind", result.stdout)

    def test_invalid_scroll_does_not_move_before_reporting_error(self):
        module = self.load("mouse")
        code, payload = self.invoke(module, "scroll", "--direction", "down", "--amount", "0", "--x", "500", "--y", "500")
        self.assertNotEqual(code, 0)
        self.assertFalse(payload["ok"])
        self.assert_no_input()

    def test_invalid_mouse_durations_do_not_trigger_input(self):
        module = self.load("mouse")
        for duration in ("-1", "nan", "inf"):
            with self.subTest(duration=duration):
                code, payload = self.invoke(module, "move-to", "--x", "500", "--y", "500", "--duration", duration)
                self.assertNotEqual(code, 0)
                self.assertFalse(payload["ok"])
                self.assert_no_input()

    def test_invalid_hold_seconds_does_not_press_mouse(self):
        module = self.load("mouse")
        with mock.patch.object(module.time, "sleep"):
            code, payload = self.invoke(module, "left-hold", "--seconds", "-2")
        self.assertNotEqual(code, 0)
        self.assertFalse(payload["ok"])
        self.assert_no_input()

    def test_mouse_hold_releases_button_after_interruption(self):
        module = self.load("mouse")
        self.gui.mouseUp.side_effect = lambda **kwargs: self.assertFalse(self.gui.FAILSAFE)
        with mock.patch.object(module.time, "sleep", side_effect=RuntimeError("interrupted")):
            code, payload = self.invoke(module, "left-hold", "--seconds", "1")
        self.assertNotEqual(code, 0)
        self.assertFalse(payload["ok"])
        self.gui.mouseDown.assert_called_once_with(button="left")
        self.gui.mouseUp.assert_called_once_with(button="left")
        self.assertTrue(self.gui.FAILSAFE)

    def test_explicit_release_of_mouse_button_works_at_a_failsafe_corner(self):
        module = self.load("mouse")
        def release(**kwargs):
            if self.gui.FAILSAFE:
                raise RuntimeError("cursor is at a failsafe corner")
        self.gui.mouseUp.side_effect = release
        code, payload = self.invoke(module, "left-up")
        self.assertEqual(code, 0, payload)
        self.assertTrue(payload["ok"])
        self.gui.mouseUp.assert_called_once_with(button="left")
        self.assertTrue(self.gui.FAILSAFE)

    def test_mouse_slide_rejects_conflicting_modes(self):
        module = self.load("mouse")
        code, payload = self.invoke(module, "slide", "--dx", "10", "--direction", "right", "--distance", "20")
        self.assertNotEqual(code, 0)
        self.assertFalse(payload["ok"])
        self.assert_no_input()

    def test_mouse_rejects_outside_primary_screen_coordinates(self):
        module = self.load("mouse")
        code, payload = self.invoke(module, "left-click", "--x", "-100", "--y", "50")
        self.assertNotEqual(code, 0)
        self.assertFalse(payload["ok"])
        self.assert_no_input()

    def test_mouse_click_and_scroll_dispatch_expected_actions(self):
        module = self.load("mouse")
        code, payload = self.invoke(module, "left-click", "--x", "500", "--y", "600")
        self.assertEqual(code, 0)
        self.assertTrue(payload["ok"])
        self.gui.moveTo.assert_called_once_with(500, 600, duration=0.0)
        self.gui.click.assert_called_once_with(button="left")
        code, payload = self.invoke(module, "scroll", "--direction", "down", "--amount", "3")
        self.assertEqual(code, 0)
        self.gui.scroll.assert_called_once_with(-3)

    def test_typing_rejects_non_ascii_before_any_input(self):
        module = self.load("typing")
        code, payload = self.invoke(module, "type", "--text", "中文 🌐")
        self.assertNotEqual(code, 0)
        self.assertFalse(payload["ok"])
        self.assert_no_input()

    def test_typing_rejects_invalid_timing_and_repeat_count(self):
        module = self.load("typing")
        cases = [("type", "--text", "hello", "--interval", "-1"),
                 ("type", "--text", "hello", "--delay", "nan"),
                 ("press", "--key", "enter", "--presses", "0"),
                 ("press", "--key", "enter", "--interval", "inf")]
        for args in cases:
            with self.subTest(args=args):
                code, payload = self.invoke(module, *args)
                self.assertNotEqual(code, 0)
                self.assertFalse(payload["ok"])
                self.assert_no_input()

    def test_hotkey_validates_all_keys_before_input(self):
        module = self.load("typing")
        code, payload = self.invoke(module, "hotkey", "--keys", "ctrl", "unsupported-key")
        self.assertNotEqual(code, 0)
        self.assertFalse(payload["ok"])
        self.assert_no_input()

    def test_hotkey_releases_pressed_keys_when_a_later_key_fails(self):
        module = self.load("typing")
        def down(key):
            if key == "c":
                raise RuntimeError("interrupted")
        self.gui.keyDown.side_effect = down
        self.gui.keyUp.side_effect = lambda key: self.assertFalse(self.gui.FAILSAFE)
        code, payload = self.invoke(module, "hotkey", "--keys", "ctrl", "c")
        self.assertNotEqual(code, 0)
        self.assertFalse(payload["ok"])
        self.assertIn(mock.call("ctrl"), self.gui.keyUp.call_args_list)
        self.assertTrue(self.gui.FAILSAFE)

    def test_explicit_release_of_key_works_at_a_failsafe_corner(self):
        module = self.load("typing")
        def release(key):
            if self.gui.FAILSAFE:
                raise RuntimeError("cursor is at a failsafe corner")
        self.gui.keyUp.side_effect = release
        code, payload = self.invoke(module, "up", "--key", "shift")
        self.assertEqual(code, 0, payload)
        self.assertTrue(payload["ok"])
        self.gui.keyUp.assert_called_once_with("shift")
        self.assertTrue(self.gui.FAILSAFE)

    def test_typing_success_and_shortcut_alias(self):
        module = self.load("typing")
        code, payload = self.invoke(module, "type", "--text", "Hello\tWorld\n")
        self.assertEqual(code, 0)
        self.assertTrue(payload["ok"])
        self.gui.write.assert_called_once_with("Hello\tWorld\n", interval=0.01)
        code, payload = self.invoke(module, "shortcut", "--keys", "cmd", "c")
        self.assertEqual(code, 0)
        self.assertEqual(payload["details"]["keys"], ["command", "c"])

    def test_screenshot_reads_live_virtual_bounds_before_capture(self):
        module = self.load("screenshot")
        desktop = module.DesktopInfo("mss", module.Rect(-1280, 0, 3201, 1080), [])
        events = []
        def resolution():
            events.append("resolution")
            return desktop
        def capture(rect, output, *args, **kwargs):
            events.append(("capture", rect))
            output.write_bytes(b"\x89PNG\r\n\x1a\n" + struct.pack(">I", 13) + b"IHDR" + struct.pack(">II", rect.width, rect.height))
            return "mss"
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch.object(module, "read_resolution", side_effect=resolution), mock.patch.object(module, "capture_rect", side_effect=capture):
                code, payload = self.invoke(module, "half", "--side", "right", "--output", str(Path(tmp) / "half.png"))
        self.assertEqual(code, 0)
        self.assertTrue(payload["ok"])
        self.assertEqual(events, ["resolution", ("capture", module.Rect(320, 0, 1601, 1080))])
        self.assertEqual(payload["left"], -1280)
        self.assertEqual(payload["region"]["left"], 320)

    def test_screenshot_prefers_modern_mss_factory_and_supports_older_versions(self):
        module = self.load("screenshot")
        for modern in (True, False):
            with self.subTest(modern=modern):
                factory = mock.MagicMock()
                factory.return_value.__enter__.return_value.monitors = [
                    {"left": 0, "top": 0, "width": 1920, "height": 1080},
                    {"left": 0, "top": 0, "width": 1920, "height": 1080},
                ]
                fake_mss = SimpleNamespace(mss=mock.Mock(side_effect=RuntimeError("deprecated factory selected"))) if modern else SimpleNamespace(mss=factory)
                if modern:
                    fake_mss.MSS = factory
                with mock.patch.dict(sys.modules, {"mss": fake_mss}), \
                        mock.patch.object(module, "_read_resolution_with_pillow", side_effect=RuntimeError("disabled in tests")), \
                        mock.patch.object(module, "_read_resolution_with_macos_screencapture", side_effect=RuntimeError("disabled in tests")):
                    code, payload = self.invoke(module, "resolution")
                self.assertEqual(code, 0, payload)
                self.assertEqual(payload["resolution"], "1920x1080")
                factory.assert_called_once_with()

    def test_invalid_screenshot_region_does_not_capture_or_create_output_directory(self):
        module = self.load("screenshot")
        desktop = module.DesktopInfo("mss", module.Rect(0, 0, 1920, 1080), [])
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "should-not-exist"
            with mock.patch.object(module, "read_resolution", return_value=desktop), mock.patch.object(module, "capture_rect") as capture:
                code, payload = self.invoke(module, "region", "--x1", "0", "--y1", "0", "--x2", "9999", "--y2", "100", "--output", str(folder / "invalid.png"))
            self.assertNotEqual(code, 0)
            self.assertFalse(payload["ok"])
            capture.assert_not_called()
            self.assertFalse(folder.exists())

    def test_screenshot_backend_failure_does_not_switch_coordinate_spaces(self):
        module = self.load("screenshot")
        desktop = module.DesktopInfo("mss", module.Rect(-1280, 0, 3200, 1080), [])
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch.object(module, "read_resolution", return_value=desktop), \
                    mock.patch.object(module, "_capture_rect_with_mss", side_effect=RuntimeError("capture failed")), \
                    mock.patch.object(module, "_capture_rect_with_pillow") as pillow:
                code, payload = self.invoke(module, "full", "--output", str(Path(tmp) / "screen.png"))
        self.assertNotEqual(code, 0)
        self.assertFalse(payload["ok"])
        pillow.assert_not_called()


if __name__ == "__main__":
    unittest.main()
