"""Code-only regression tests for keyboard input validation."""

import importlib.util
import io
from pathlib import Path
import sys
import unittest
from unittest.mock import Mock, patch


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "webuse_typing.py"
SPEC = importlib.util.spec_from_file_location("webuse_typing_test", SCRIPT)
typing = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = typing
SPEC.loader.exec_module(typing)


class TypingTests(unittest.TestCase):
    def test_control_characters_are_rejected(self):
        for text in ("line\n", "tab\t", "return\r"):
            with self.subTest(text=text), self.assertRaisesRegex(ValueError, "control characters"):
                typing.validate_text(text)

    def test_primary_modifier_is_platform_aware(self):
        with patch.object(typing.platform, "system", return_value="Darwin"):
            self.assertEqual(typing.normalize_key("primary"), "command")
        with patch.object(typing.platform, "system", return_value="Windows"):
            self.assertEqual(typing.normalize_key("primary"), "ctrl")

    def test_nonpositive_press_count_is_rejected(self):
        with self.assertRaises(SystemExit):
            typing.build_parser().parse_args(["press", "--key", "a", "--presses", "0"])

    def test_stdin_removes_one_shell_record_terminator(self):
        fake = Mock()
        fake.FAILSAFE = True
        args = typing.build_parser().parse_args(["type", "--stdin"])
        with patch.object(typing, "pyautogui", fake), \
             patch.object(sys, "stdin", io.StringIO("hello\n")):
            result = typing.action_type(args)
        fake.write.assert_called_once_with("hello", interval=0.01)
        self.assertEqual(result.details["length"], 5)


if __name__ == "__main__":
    unittest.main()
