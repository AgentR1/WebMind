"""Regression tests for native mouse-pointer capture."""

import contextlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import Mock, patch


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "webuse_screenshot.py"
SPEC = importlib.util.spec_from_file_location("webuse_screenshot", SCRIPT)
screenshot = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = screenshot
SPEC.loader.exec_module(screenshot)


class CursorCaptureTests(unittest.TestCase):
    def test_open_mss_prefers_new_factory_and_enables_cursor(self):
        instance = object()
        factory = Mock(return_value=instance)
        fake_mss = types.ModuleType("mss")
        fake_mss.MSS = factory

        with patch.dict(sys.modules, {"mss": fake_mss}):
            result = screenshot._open_mss(with_cursor=True)

        self.assertIs(result, instance)
        factory.assert_called_once_with(with_cursor=True)

    def test_open_mss_supports_legacy_instance_property(self):
        class LegacyCapture:
            with_cursor = False

        instance = LegacyCapture()
        calls = []

        def legacy_factory(**kwargs):
            calls.append(kwargs)
            if kwargs:
                raise TypeError("old constructor")
            return instance

        fake_mss = types.ModuleType("mss")
        fake_mss.mss = legacy_factory

        with patch.dict(sys.modules, {"mss": fake_mss}):
            result = screenshot._open_mss(with_cursor=True)

        self.assertIs(result, instance)
        self.assertTrue(instance.with_cursor)
        self.assertEqual(calls, [{"with_cursor": True}, {}])

    def test_screenshot_commands_request_cursor_by_default(self):
        parser = screenshot.build_parser()
        commands = (
            ["full"],
            ["half", "--side", "left"],
            ["region", "--x1", "0", "--y1", "0", "--x2", "10", "--y2", "10"],
        )
        for argv in commands:
            with self.subTest(argv=argv):
                self.assertFalse(parser.parse_args(argv).no_cursor)
                self.assertTrue(parser.parse_args([*argv, "--no-cursor"]).no_cursor)

    def run_main(self, argv, backend, *, native_cursor=False, overlay=None):
        desktop = screenshot.DesktopInfo(
            backend="mss",
            rect=screenshot.Rect(left=0, top=0, width=100, height=100),
            monitors=[],
        )
        stdout = io.StringIO()
        if overlay is None:
            overlay = {
                "requested": True,
                "included": True,
                "source": "system-position-overlay",
                "position": {"x": 10, "y": 10, "coordinate_space": "desktop-absolute-pixels"},
                "image_point": {"x": 10, "y": 10},
                "kind": "pointer-marker",
                "reason": None,
            }
        def fake_capture(region, output, **kwargs):
            from PIL import Image
            Image.new("RGB", (region.width, region.height)).save(output)
            return backend, native_cursor
        with tempfile.TemporaryDirectory(prefix="webuse-capture-fixture-") as temp, \
             patch.object(screenshot, "_ensure_output_path", return_value=Path(temp) / "capture.png"), \
             patch.object(screenshot, "read_resolution", return_value=desktop), \
             patch.object(screenshot, "capture_rect", side_effect=fake_capture) as capture, \
             patch.object(screenshot, "_read_pointer_position", return_value=(10, 10)), \
             patch.object(screenshot, "_overlay_cursor_marker", return_value=overlay) as cursor_overlay, \
             contextlib.redirect_stdout(stdout):
            return_code = screenshot.main([*argv, "--json"])
        return return_code, json.loads(stdout.getvalue()), capture, cursor_overlay

    def test_main_reports_native_cursor_capture(self):
        code, payload, capture, cursor_overlay = self.run_main(
            ["full", "--output", "ignored.png"], "mss", native_cursor=True
        )

        self.assertEqual(code, 0)
        capture.assert_called_once()
        self.assertTrue(capture.call_args.kwargs["with_cursor"])
        cursor_overlay.assert_not_called()
        self.assertEqual(
            payload["cursor"],
            {"requested": True, "included": True, "source": "mss-native", "reason": None},
        )
        self.assertNotIn("warnings", payload)

    def test_main_adds_cursor_overlay_when_backend_is_not_native(self):
        code, payload, _, cursor_overlay = self.run_main(
            ["full", "--output", "ignored.png"], "pillow_imagegrab"
        )

        self.assertEqual(code, 0)
        cursor_overlay.assert_called_once()
        self.assertTrue(payload["cursor"]["requested"])
        self.assertTrue(payload["cursor"]["included"])
        self.assertEqual(payload["cursor"]["source"], "system-position-overlay")
        self.assertNotIn("warnings", payload)

    def test_main_warns_when_pointer_is_outside_crop(self):
        overlay = {
            "requested": True,
            "included": False,
            "source": "system-position-overlay",
            "position": {"x": 200, "y": 200, "coordinate_space": "desktop-absolute-pixels"},
            "reason": "outside-capture-region",
        }
        code, payload, _, _ = self.run_main(
            ["full", "--output", "ignored.png"], "mss", overlay=overlay
        )

        self.assertEqual(code, 0)
        self.assertFalse(payload["cursor"]["included"])
        self.assertIn("outside-capture-region", payload["warnings"][0])

    def test_no_cursor_disables_native_capture(self):
        code, payload, capture, cursor_overlay = self.run_main(
            ["full", "--no-cursor", "--output", "ignored.png"], "mss"
        )

        self.assertEqual(code, 0)
        self.assertFalse(capture.call_args.kwargs["with_cursor"])
        cursor_overlay.assert_not_called()
        self.assertEqual(
            payload["cursor"],
            {"requested": False, "included": False, "source": None, "reason": "disabled"},
        )

    def test_overlay_places_marker_tip_at_pointer_coordinate(self):
        from PIL import Image, ImageChops

        with tempfile.TemporaryDirectory(prefix="webuse-screenshot-test-") as directory:
            output = Path(directory) / "capture.png"
            Image.new("RGB", (100, 100), "white").save(output)
            with patch.object(screenshot, "_read_pointer_position", return_value=(25, 30)):
                result = screenshot._overlay_cursor_marker(
                    output, screenshot.Rect(left=10, top=10, width=100, height=100)
                )
            with Image.open(output) as rendered:
                marker = rendered.convert("RGB").crop((15, 20, 40, 53))
                blank = Image.new("RGB", marker.size, "white")
                self.assertIsNotNone(ImageChops.difference(marker, blank).getbbox())

        self.assertTrue(result["included"])
        self.assertEqual(result["image_point"], {"x": 15, "y": 20})
        self.assertEqual(result["position"]["coordinate_space"], "desktop-absolute-pixels")

    def test_macos_native_fallback_returns_capture_contract_tuple(self):
        region = screenshot.Rect(left=0, top=0, width=10, height=10)
        with patch.object(screenshot, "_capture_rect_with_mss", side_effect=RuntimeError("no mss")), \
             patch.object(screenshot, "_capture_rect_with_pillow", side_effect=RuntimeError("no pillow")), \
             patch.object(screenshot.platform, "system", return_value="Darwin"), \
             patch.object(screenshot, "_capture_rect_with_macos_screencapture", return_value="macos_screencapture"):
            result = screenshot.capture_rect(region, Path("capture.png"))

        self.assertEqual(result, ("macos_screencapture", False))


if __name__ == "__main__":
    unittest.main()
