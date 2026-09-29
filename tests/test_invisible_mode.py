"""Browser-mode regression checks with no live browser or user Profile access."""
from __future__ import annotations

from contextlib import ExitStack
import importlib.util
import io
import json
from pathlib import Path
import unittest
from unittest.mock import Mock, mock_open, patch


SCRIPT = Path(__file__).resolve().parents[1] / "skills/webmind-cdp/scripts/webmind_cdp.py"
spec = importlib.util.spec_from_file_location("webmind_cdp_test", SCRIPT)
cdp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cdp)


class InvisibleModeTests(unittest.TestCase):
    def setUp(self):
        # Only path identity is needed; no Profile or runtime files are created.
        self.profile = Path(__file__).resolve().parent / "fixture-42-mem-Profile"
        self.config = {
            "endpoint": "http://127.0.0.1:9042",
            "profile_path": str(self.profile),
            "debug_port": 9042,
            "mem_path": str(self.profile.parent),
            "profile_metadata": str(self.profile / "webmind-profile.json"),
        }
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.stack.enter_context(patch.object(Path, "mkdir"))
        self.stack.enter_context(patch.object(cdp.platform, "platform", return_value="Darwin-test"))
        self.stack.enter_context(patch.object(cdp, "load_browser_configuration", return_value=self.config))
        self.process = self.stack.enter_context(patch.object(cdp.subprocess, "run"))
        self.process.return_value.returncode = 0
        chrome = str(self.profile.parent / "Chrome.app/Contents/MacOS/Chrome")
        self.stack.enter_context(patch.object(cdp, "find_chrome_executable", return_value=chrome))
        self.stack.enter_context(patch.object(cdp, "macos_chrome_executable", return_value=chrome))
        self.stack.enter_context(patch.object(cdp.tempfile, "mkstemp", return_value=(123, "test-launch.log")))
        self.stack.enter_context(patch.object(cdp.os, "fdopen", mock_open()))
        self.version = {"webSocketDebuggerUrl": "ws://127.0.0.1:9042/devtools/browser/test"}
        self.client = Mock()
        self.stack.enter_context(patch.object(cdp, "CDPClient", return_value=self.client))
        self.get_version = self.stack.enter_context(patch.object(cdp, "get_version", return_value=self.version))
        self.get_tabs = self.stack.enter_context(patch.object(cdp, "get_tabs", return_value=[]))

    def args(self, invisible=False, command=None):
        argv = (["--invisible-mode"] if invisible else []) + (command or ["launch"])
        return cdp.build_parser().parse_args(argv)

    def report_browser(self, invisible=False, profile=None):
        arguments = ["chrome.exe", f"--user-data-dir={profile or self.profile}"]
        if invisible:
            arguments.append("--headless")
        self.client.call.return_value = {"arguments": arguments}
        return arguments

    def test_default_launch_has_no_invisible_flags(self):
        cdp.launch_chrome(self.args())
        command = self.process.call_args.args[0]
        self.assertFalse(any(arg.startswith("--headless") for arg in command))
        self.assertIn(f"--user-data-dir={self.profile}", command)
        self.assertIn("--remote-debugging-address=127.0.0.1", command)

    def test_invisible_launch_keeps_bound_profile_and_redacts_url(self):
        args = self.args(True, ["launch", "--url", "https://example.com/private-test"])
        result = cdp.launch_chrome(args)
        command = self.process.call_args.args[0]
        self.assertIn("--headless", command)
        self.assertIn("--enable-automation", command)
        self.assertIn("--remote-debugging-port=9042", command)
        self.assertIn(f"--user-data-dir={self.profile}", command)
        self.assertEqual(result["requested_browser_mode"], "invisible")
        self.assertEqual(result["command"][-1], "<redacted-url>")

    def test_invisible_choice_does_not_carry_to_next_invocation(self):
        cdp.launch_chrome(self.args(True))
        cdp.launch_chrome(self.args())
        self.assertNotIn("--headless", self.process.call_args.args[0])
        self.assertNotIn("invisible_mode", self.config)

    def test_new_tab_background_flag_does_not_select_browser_mode(self):
        args = self.args(command=["new-tab", "--background"])
        self.assertTrue(args.background)
        self.assertEqual(cdp.requested_browser_mode(args), "visible")

    def test_invisible_mode_rejects_new_window_before_launch(self):
        with self.assertRaisesRegex(ValueError, "--new-window"):
            cdp.command_launch(self.args(True, ["launch", "--new-window"]))
        self.process.assert_not_called()
        self.get_version.assert_not_called()

    def test_actual_mode_uses_switches_not_urls_or_arguments_after_terminator(self):
        for switch in ("--headless", "--headless=new", "-headless"):
            with self.subTest(switch=switch):
                self.assertEqual(cdp.browser_mode_from_arguments(["chrome.exe", switch]), "invisible")
        for arguments in (
            ["chrome.exe", "https://example.com/--headless"],
            ["chrome.exe", "--", "--headless"],
            ["chrome.exe", "--headless-other"],
            ["chrome.exe", "--HEADLESS"],
            ["chrome.exe", "/headless"],
        ):
            with self.subTest(arguments=arguments):
                self.assertEqual(cdp.browser_mode_from_arguments(arguments), "visible")

    def test_matching_existing_browser_is_reused_in_both_modes(self):
        for invisible in (False, True):
            with self.subTest(invisible=invisible):
                self.report_browser(invisible)
                result = cdp.ensure_endpoint(self.args(invisible))
                self.assertIsNone(result["launch"])
                self.assertEqual(result["browser_mode"], "invisible" if invisible else "visible")
        self.process.assert_not_called()

    def test_both_mode_mismatches_refuse_reuse_and_relaunch(self):
        for requested in (False, True):
            with self.subTest(requested=requested):
                self.report_browser(not requested)
                with self.assertRaisesRegex(RuntimeError, "browser mode mismatch"):
                    cdp.ensure_endpoint(self.args(requested))
        self.process.assert_not_called()
        self.assertFalse(any(call.args[0] == "Browser.close" for call in self.client.call.call_args_list))

    def test_invisible_mode_does_not_bypass_profile_verification(self):
        self.report_browser(True, self.profile.parent / "unrelated-profile")
        with self.assertRaisesRegex(RuntimeError, "profile mismatch"):
            cdp.ensure_endpoint(self.args(True))
        self.process.assert_not_called()

    def test_unverifiable_browser_does_not_trigger_launch(self):
        self.client.call.side_effect = RuntimeError("no browser identity")
        with self.assertRaisesRegex(RuntimeError, "cannot verify CDP profile"):
            cdp.ensure_endpoint(self.args(True))
        self.process.assert_not_called()

    def test_posix_requires_browser_arguments_without_command_line_fallback(self):
        self.client.call.side_effect = RuntimeError("not available")
        with self.assertRaisesRegex(RuntimeError, "cannot verify CDP profile"):
            cdp.ensure_endpoint(self.args(True))
        self.client.call.assert_called_once_with("Browser.getBrowserCommandLine")
        self.process.assert_not_called()

    def test_invisible_flags_reach_launchservices_helper(self):
        result = cdp.launch_chrome(self.args(True))
        command = self.process.call_args.args[0]
        self.assertEqual(command[0], "/bin/bash")
        self.assertTrue(command[1].endswith("launch_chrome_macos.sh"))
        self.assertTrue(command[2].endswith("Chrome.app"))
        self.assertEqual(command.count("--enable-automation"), 1)
        self.assertIn("--headless", command)
        self.assertIn("--window-size=1280,800", command)
        self.assertEqual(result["command"][:2], ["/usr/bin/open", "-na"])
        self.assertEqual(result["launcher"], "macos-open")

    def test_auto_launch_honors_invisible_choice_and_verifies_result(self):
        self.get_version.side_effect = [OSError("not running"), self.version]
        self.report_browser(True)
        with patch.object(cdp, "wait_for_endpoint", return_value=True):
            result = cdp.ensure_endpoint(self.args(True, ["tabs"]))
        self.assertIn("--headless", self.process.call_args.args[0])
        self.assertEqual(result["browser_mode"], "invisible")

    def test_newly_launched_wrong_mode_is_not_retried(self):
        self.get_version.side_effect = [OSError("not running"), self.version]
        self.report_browser(False)
        with patch.object(cdp, "wait_for_endpoint", return_value=True):
            with self.assertRaisesRegex(RuntimeError, "browser mode mismatch"):
                cdp.ensure_endpoint(self.args(True))
        self.process.assert_called_once()

    def test_no_auto_launch_is_preserved(self):
        self.get_version.side_effect = OSError("not running")
        args = cdp.build_parser().parse_args(["--invisible-mode", "--no-auto-launch", "tabs"])
        with self.assertRaises(OSError):
            cdp.ensure_endpoint(args)
        self.process.assert_not_called()

    def test_self_check_never_launches_on_mode_mismatch(self):
        self.report_browser(True)
        result = cdp.command_self_check(self.args(command=["self-check"]))
        self.assertFalse(result["ok"])
        self.assertIn("browser mode mismatch", result["error"])
        self.get_tabs.assert_not_called()
        self.process.assert_not_called()

    def test_mode_mismatch_stops_page_actions(self):
        self.report_browser(True)
        args = self.args(command=["eval", "--target-id", "test", "--expression", "document.title"])
        with self.assertRaisesRegex(RuntimeError, "browser mode mismatch"):
            cdp.command_eval(args)
        self.get_tabs.assert_not_called()
        self.assertFalse(any(call.args[0] == "Runtime.evaluate" for call in self.client.call.call_args_list))

    def test_cli_reports_verified_mode(self):
        self.report_browser(True)
        with patch.object(cdp.sys, "argv", [str(SCRIPT), "--invisible-mode", "tabs", "--json"]), \
                patch.object(cdp.platform, "system", return_value="Darwin"), \
                patch.object(cdp, "configure_utf8_stdio"), patch("sys.stdout", new_callable=io.StringIO) as output:
            self.assertEqual(cdp.main(), 0)
            result = json.loads(output.getvalue())
        self.assertEqual(result["browser_mode"], "invisible")
        self.assertEqual(result["requested_browser_mode"], "invisible")


if __name__ == "__main__":
    unittest.main()
