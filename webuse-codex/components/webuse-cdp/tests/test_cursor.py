"""CDP cursor command and screenshot failure regression tests."""

import base64
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from test_profile_verification import cdp


class CursorTests(unittest.TestCase):
    def args(self, *argv):
        return cdp.build_parser().parse_args(list(argv))

    def test_move_requires_complete_coordinates_without_connecting(self):
        for argv in (("move",), ("move", "--x", "3"),
                     ("move", "--selector", "button", "--y", "3")):
            with self.subTest(argv=argv), patch.object(cdp, "connect_target") as connect:
                with self.assertRaises(ValueError):
                    cdp.command_move(self.args(*argv))
                connect.assert_not_called()

    def test_nonfinite_coordinates_do_not_send_mouse_events(self):
        for x, y in ((float("nan"), 1), (1, float("inf"))):
            client = Mock()
            with self.assertRaises(ValueError):
                cdp.move_cdp_pointer(client, x, y)
            client.call.assert_not_called()

    def test_coordinates_outside_viewport_do_not_send_mouse_events(self):
        for x, y in ((-1, 0), (800, 0), (0, 600)):
            with patch.object(cdp, "cursor_context", return_value=7), patch.object(
                cdp, "runtime_evaluate", return_value={"width": 800, "height": 600}
            ):
                client = Mock()
                with self.assertRaises(ValueError):
                    cdp.move_cdp_pointer(client, x, y)
                client.call.assert_not_called()

    def test_failed_mouse_dispatch_does_not_record_position(self):
        client = Mock()
        client.call.side_effect = RuntimeError("dispatch failed")
        with patch.object(cdp, "cursor_context", return_value=7), patch.object(
            cdp, "runtime_evaluate", return_value={"width": 800, "height": 600}
        ) as evaluate:
            with self.assertRaisesRegex(RuntimeError, "dispatch failed"):
                cdp.move_cdp_pointer(client, 40, 60)
            evaluate.assert_called_once()

    def test_move_records_only_successful_dispatch_and_never_clicks(self):
        client = Mock()
        with patch.object(cdp, "cursor_context", return_value=7), patch.object(
            cdp, "runtime_evaluate", return_value={"width": 800, "height": 600}
        ):
            point = cdp.move_cdp_pointer(client, 40.5, 60.5)
        client.call.assert_called_once_with("Input.dispatchMouseEvent", {"type": "mouseMoved", "x": 40.5, "y": 60.5})
        self.assertEqual(point["source"], "cdp")
        self.assertEqual(point["coordinate_space"], "viewport-css-pixels")

    def test_screenshot_failure_closes_client_without_mutating_dom(self):
        client = Mock()
        client.call.side_effect = RuntimeError("capture failed")
        with patch.object(cdp, "connect_target", return_value=(client, {})), \
             patch.object(cdp, "cursor_context", return_value=7), \
             patch.object(cdp, "read_cdp_pointer", return_value={"drawn": False}), \
             patch.object(cdp, "annotate_cdp_screenshot") as annotate:
            with self.assertRaisesRegex(RuntimeError, "capture failed"):
                cdp.command_screenshot(self.args("screenshot"))
            annotate.assert_not_called()
            client.close.assert_called_once()

    def test_unknown_cursor_state_failure_is_not_reported_as_screenshot_success(self):
        client = Mock()
        with patch.object(cdp, "connect_target", return_value=(client, {})), \
             patch.object(cdp, "cursor_context", return_value=7), \
             patch.object(cdp, "read_cdp_pointer", side_effect=RuntimeError("cursor state failed")):
            with self.assertRaisesRegex(RuntimeError, "cursor state failed"):
                cdp.command_screenshot(self.args("screenshot"))
            client.call.assert_not_called()
            client.close.assert_called_once()

    def test_no_cursor_preserves_original_screenshot_and_needs_no_cursor_context(self):
        client = Mock()
        raw = b"unchanged screenshot bytes"
        client.call.return_value = {"data": base64.b64encode(raw).decode()}
        with tempfile.TemporaryDirectory(prefix="webuse-cursor-unit-") as directory:
            output = Path(directory) / "page.png"
            with patch.object(cdp, "connect_target", return_value=(client, {})), \
                 patch.object(cdp, "cursor_context") as context:
                result = cdp.command_screenshot(self.args("screenshot", "--no-cursor", "--output", str(output)))
            context.assert_not_called()
            self.assertEqual(output.read_bytes(), raw)
        self.assertEqual(result["cursor"]["reason"], "disabled")

    def test_unknown_position_has_explicit_warning(self):
        client = Mock()
        client.call.return_value = {"data": base64.b64encode(b"png").decode()}
        with tempfile.TemporaryDirectory(prefix="webuse-cursor-unit-") as directory:
            with patch.object(cdp, "connect_target", return_value=(client, {})), \
                 patch.object(cdp, "cursor_context", return_value=7), \
                 patch.object(cdp, "read_cdp_pointer", return_value={"drawn": False, "source": "cdp", "reason": "unknown-position"}):
                result = cdp.command_screenshot(self.args("screenshot", "--output", str(Path(directory) / "page.png")))
        self.assertTrue(result["ok"])
        self.assertFalse(result["cursor"]["drawn"])
        self.assertIn("unknown-position", result["warnings"][0])

    def test_changed_position_is_not_drawn(self):
        client = Mock()
        raw = b"unchanged screenshot bytes"
        client.call.return_value = {"data": base64.b64encode(raw).decode()}
        with tempfile.TemporaryDirectory(prefix="webuse-cursor-unit-") as directory:
            output = Path(directory) / "page.png"
            with patch.object(cdp, "connect_target", return_value=(client, {})), \
                 patch.object(cdp, "cursor_context", return_value=7), \
                 patch.object(cdp, "read_cdp_pointer", side_effect=[{"x": 20}, {"x": 30}]):
                result = cdp.command_screenshot(self.args("screenshot", "--output", str(output)))
            self.assertEqual(output.read_bytes(), raw)
        self.assertEqual(result["cursor"]["reason"], "pointer-or-viewport-changed")


if __name__ == "__main__":
    unittest.main()
