"""Offline checks for the public WebMind command-line interface."""

import argparse
import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "webmind.py"


def load_webmind():
    spec = importlib.util.spec_from_file_location("webmind_under_test", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class WebMindTests(unittest.TestCase):
    def test_cli_help(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--help"],
            capture_output=True, text=True, timeout=10,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("WebMind", result.stdout)
        self.assertIn("wait-for-selector", result.stdout)

    def test_profile_environment_can_override_the_default(self):
        module = load_webmind()
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch.dict(os.environ, {"WEBMIND_PROFILE": tmp}):
                args = module.build_parser().parse_args(["self-check"])
            self.assertEqual(module.resolve_profile_dir(args.user_data_dir), Path(tmp).resolve())

    def test_chrome_environment_can_select_an_executable(self):
        module = load_webmind()
        with tempfile.TemporaryDirectory() as tmp:
            executable = Path(tmp) / "custom-chrome"
            executable.touch()
            with mock.patch.dict(os.environ, {"WEBMIND_CHROME": str(executable)}):
                self.assertEqual(module.find_chrome_executable(), str(executable))

    def test_self_check_reports_unavailable_endpoint_without_launching(self):
        module = load_webmind()
        args = module.build_parser().parse_args(["self-check"])
        with mock.patch.object(module, "get_version", side_effect=ConnectionError("unavailable")):
            with mock.patch.object(module, "launch_chrome") as launch:
                result = module.command_self_check(args)
        self.assertFalse(result["ok"])
        self.assertIn("unavailable", result["error"])
        launch.assert_not_called()

    def test_no_auto_launch_preserves_an_unavailable_endpoint(self):
        module = load_webmind()
        args = module.build_parser().parse_args(["--no-auto-launch", "tabs"])
        with mock.patch.object(module, "get_version", side_effect=ConnectionError("unavailable")):
            with mock.patch.object(module, "launch_chrome") as launch:
                with self.assertRaises(ConnectionError):
                    module.ensure_endpoint(args)
        launch.assert_not_called()

    def test_remote_endpoint_cannot_trigger_local_browser_launch(self):
        module = load_webmind()
        args = argparse.Namespace(endpoint="http://remote.invalid:9222")
        with mock.patch.object(module.subprocess, "Popen") as popen:
            with self.assertRaisesRegex(RuntimeError, "non-local endpoint"):
                module.launch_chrome(args)
        popen.assert_not_called()

    def test_target_id_selects_the_requested_page(self):
        module = load_webmind()
        args = module.build_parser().parse_args([
            "eval", "--target-id", "second", "--expression", "document.title",
        ])
        tabs = [
            {"id": "first", "type": "page", "webSocketDebuggerUrl": "ws://local/first"},
            {"id": "second", "type": "page", "webSocketDebuggerUrl": "ws://local/second"},
        ]
        with mock.patch.object(module, "ensure_endpoint"):
            with mock.patch.object(module, "get_tabs", return_value=tabs):
                self.assertEqual(module.select_tab(args)["id"], "second")

    def test_missing_target_fails_instead_of_selecting_another_page(self):
        module = load_webmind()
        args = module.build_parser().parse_args([
            "eval", "--target-id", "missing", "--expression", "document.title",
        ])
        tabs = [{"id": "first", "type": "page", "webSocketDebuggerUrl": "ws://local/first"}]
        with mock.patch.object(module, "ensure_endpoint"):
            with mock.patch.object(module, "get_tabs", return_value=tabs):
                with self.assertRaisesRegex(RuntimeError, "no CDP tab found with id"):
                    module.select_tab(args)


if __name__ == "__main__":
    unittest.main()
