"""Regression tests for endpoint/profile ownership; never operate a real browser."""

import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "webuse_cdp.py"
SPEC = importlib.util.spec_from_file_location("webuse_cdp", SCRIPT)
cdp = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(cdp)


class ProfileVerificationTests(unittest.TestCase):
    def setUp(self):
        self.expected = (SCRIPT.parent / "test profiles" / "中文 profile").resolve()
        self.other = self.expected.parent / "other"
        self.version = {"webSocketDebuggerUrl": "ws://127.0.0.1:9222/devtools/browser/test"}
        self.stack = contextlib.ExitStack()
        self.addCleanup(self.stack.close)
        self.version_mock = self.stack.enter_context(patch.object(cdp, "get_version", return_value=self.version))
        self.tabs_mock = self.stack.enter_context(patch.object(cdp, "get_tabs", return_value=[]))
        self.launch_mock = self.stack.enter_context(patch.object(cdp, "launch_chrome", return_value={"pid": 123}))
        self.wait_mock = self.stack.enter_context(patch.object(cdp, "wait_for_endpoint", return_value=True))
        self.client_type = self.stack.enter_context(patch.object(cdp, "CDPClient"))
        self.client = self.client_type.return_value
        self.report_profile(self.expected)

    def args(self, *arguments):
        return cdp.build_parser().parse_args(["--user-data-dir", str(self.expected), *arguments])

    def report_profile(self, profile):
        self.client.call.side_effect = None
        self.client.call.return_value = {"arguments": ["chrome", f"--user-data-dir={profile}"]}

    def test_matching_existing_browser_is_reused_and_verified(self):
        result = cdp.command_launch(self.args("launch"))
        self.assertTrue(result["already_running"])
        self.assertTrue(result["profile_verified"])
        self.assertEqual(result["profile"], str(self.expected))
        self.assertIsNone(result["launch"])
        self.launch_mock.assert_not_called()
        self.client_type.assert_called_once_with(self.version["webSocketDebuggerUrl"], timeout=10.0)
        self.client.close.assert_called_once()

    def test_wrong_existing_browser_is_rejected_without_launch_or_tab_access(self):
        self.report_profile(self.other)
        with self.assertRaisesRegex(RuntimeError, "CDP profile mismatch") as error:
            cdp.command_launch(self.args("launch"))
        self.assertIn(str(self.expected), str(error.exception))
        self.assertIn(str(self.other), str(error.exception))
        self.launch_mock.assert_not_called()
        self.tabs_mock.assert_not_called()

    def test_no_auto_launch_still_verifies_existing_endpoint(self):
        self.report_profile(self.other)
        with self.assertRaisesRegex(RuntimeError, "profile mismatch"):
            cdp.command_tabs(self.args("--no-auto-launch", "tabs"))
        self.launch_mock.assert_not_called()
        self.tabs_mock.assert_not_called()

    def test_page_actions_are_blocked_before_target_connection(self):
        self.report_profile(self.other)
        for argv in (
            ("navigate", "--url", "https://example.com"),
            ("eval", "--expression", "document.title"),
            ("click", "--selector", "button"),
            ("move", "--selector", "button"),
            ("fill", "--selector", "input", "--text", "hello"),
            ("screenshot",),
        ):
            with self.subTest(command=argv[0]):
                args = self.args(*argv)
                with self.assertRaisesRegex(RuntimeError, "profile mismatch"):
                    args.func(args)
        self.tabs_mock.assert_not_called()
        self.launch_mock.assert_not_called()
        self.assertTrue(all(call.args[0] == "Browser.getBrowserCommandLine" for call in self.client.call.call_args_list))

    def test_default_profile_is_also_checked(self):
        self.report_profile(cdp.DEFAULT_PROFILE_DIR)
        result = cdp.command_launch(cdp.build_parser().parse_args(["launch"]))
        self.assertEqual(result["profile"], str(cdp.DEFAULT_PROFILE_DIR.resolve()))

    def test_env_profile_is_checked(self):
        with patch.dict(os.environ, {"WEBUSE_CDP_PROFILE": str(self.expected)}):
            args = cdp.build_parser().parse_args(["launch"])
        self.assertTrue(cdp.command_launch(args)["profile_verified"])

    def test_normalized_equivalent_paths_match(self):
        self.report_profile(self.expected / "child" / "..")
        result = cdp.command_launch(self.args("launch"))
        self.assertEqual(result["profile"], str(self.expected))

    @unittest.skipUnless(os.name == "nt", "Windows path comparison")
    def test_windows_case_and_separators_match_but_actual_path_is_reported(self):
        actual = str(self.expected).upper().replace("\\", "/")
        self.report_profile(actual)
        result = cdp.command_launch(self.args("launch"))
        self.assertEqual(result["profile"], str(Path(actual).resolve()))

    def test_custom_port_is_verified(self):
        cdp.command_launch(self.args("launch", "--port", "9333"))
        self.version_mock.assert_called_once_with("http://127.0.0.1:9333")

    def test_automatic_launch_is_verified_after_readiness(self):
        self.version_mock.side_effect = [ConnectionRefusedError(), self.version]
        result = cdp.command_tabs(self.args("tabs"))
        self.assertTrue(result["profile_verified"])
        self.assertEqual(result["auto_launch"], {"pid": 123})
        self.launch_mock.assert_called_once()
        self.wait_mock.assert_called_once()

    def test_explicit_launch_works_even_with_no_auto_launch(self):
        self.version_mock.side_effect = [ConnectionRefusedError(), self.version]
        result = cdp.command_launch(self.args("--no-auto-launch", "launch"))
        self.assertFalse(result["already_running"])
        self.launch_mock.assert_called_once()

    def test_newly_reachable_wrong_profile_is_rejected(self):
        self.version_mock.side_effect = [ConnectionRefusedError(), self.version]
        self.report_profile(self.other)
        with self.assertRaisesRegex(RuntimeError, "profile mismatch"):
            cdp.command_launch(self.args("launch"))
        self.launch_mock.assert_called_once()
        self.tabs_mock.assert_not_called()

    def test_newly_reachable_unknown_profile_is_rejected(self):
        self.version_mock.side_effect = [ConnectionRefusedError(), self.version]
        self.version.pop("webSocketDebuggerUrl")
        with self.assertRaisesRegex(RuntimeError, "cannot verify CDP profile"):
            cdp.command_launch(self.args("launch"))
        self.launch_mock.assert_called_once()
        self.tabs_mock.assert_not_called()

    def test_offline_no_auto_launch_does_not_start_browser(self):
        self.version_mock.side_effect = ConnectionRefusedError()
        with self.assertRaises(ConnectionRefusedError):
            cdp.command_tabs(self.args("--no-auto-launch", "tabs"))
        self.launch_mock.assert_not_called()
        self.client_type.assert_not_called()

    def test_launch_timeout_does_not_report_success(self):
        self.version_mock.side_effect = ConnectionRefusedError()
        self.wait_mock.return_value = False
        with self.assertRaisesRegex(RuntimeError, "endpoint was not ready"):
            cdp.command_launch(self.args("launch"))
        self.client_type.assert_not_called()
        self.tabs_mock.assert_not_called()

    def test_unverifiable_browser_is_rejected_without_retry_or_private_output(self):
        self.client.call.side_effect = RuntimeError("private command line must not be printed")
        with self.assertRaisesRegex(RuntimeError, "cannot verify CDP profile") as error:
            cdp.command_launch(self.args("launch"))
        self.assertNotIn("private command line", str(error.exception))
        self.launch_mock.assert_not_called()
        self.tabs_mock.assert_not_called()
        self.client.close.assert_called_once()

    def test_missing_browser_websocket_is_rejected(self):
        self.version.pop("webSocketDebuggerUrl")
        with self.assertRaisesRegex(RuntimeError, "cannot verify CDP profile"):
            cdp.command_launch(self.args("launch"))
        self.client_type.assert_not_called()
        self.launch_mock.assert_not_called()

    @unittest.skipUnless(os.name == "nt", "Windows command-line fallback")
    def test_existing_browser_without_automation_flag_uses_system_info(self):
        arguments = [r"C:\Program Files\Chrome\chrome.exe", f"--user-data-dir={self.expected}", "https://example.com"]
        self.client.call.side_effect = [
            RuntimeError("--enable-automation is not set"),
            {"commandLine": subprocess.list2cmdline(arguments)},
        ]
        result = cdp.command_launch(self.args("launch"))
        self.assertTrue(result["profile_verified"])
        self.client.call.assert_any_call("SystemInfo.getInfo")
        self.launch_mock.assert_not_called()

    @unittest.skipUnless(os.name == "nt", "Windows command-line fallback")
    def test_windows_fallback_wrong_profile_is_rejected(self):
        self.client.call.side_effect = [
            RuntimeError("--enable-automation is not set"),
            {"commandLine": subprocess.list2cmdline(["chrome", f"--user-data-dir={self.other}"])},
        ]
        with self.assertRaisesRegex(RuntimeError, "profile mismatch"):
            cdp.command_launch(self.args("launch"))
        self.launch_mock.assert_not_called()

    def test_self_check_failure_never_claims_expected_profile_is_actual(self):
        self.report_profile(self.other)
        result = cdp.command_self_check(self.args("self-check"))
        self.assertFalse(result["ok"])
        self.assertFalse(result["profile_verified"])
        self.assertIsNone(result["profile"])
        self.assertEqual(result["expected_profile"], str(self.expected))
        self.launch_mock.assert_not_called()
        self.tabs_mock.assert_not_called()

    def test_self_check_success_reports_verified_profile(self):
        result = cdp.command_self_check(self.args("self-check"))
        self.assertTrue(result["ok"])
        self.assertTrue(result["profile_verified"])
        self.assertEqual(result["profile"], str(self.expected))

    def test_cli_mismatch_returns_failure_json_and_nonzero_exit(self):
        self.report_profile(self.other)
        stdout = io.StringIO()
        with patch("sys.argv", [str(SCRIPT), "--user-data-dir", str(self.expected), "launch", "--json"]):
            with contextlib.redirect_stdout(stdout), self.assertRaises(SystemExit) as error:
                cdp.main()
        self.assertEqual(error.exception.code, 1)
        payload = json.loads(stdout.getvalue())
        self.assertFalse(payload["ok"])
        self.assertIn("profile mismatch", payload["error"])
        self.assertNotIn("profile", payload)

    def test_ambiguous_or_missing_profile_arguments_are_rejected(self):
        for arguments in (
            [], ["chrome"], ["chrome", "--user-data-dir="],
            ["chrome", "--user-data-dir=relative/path"],
            ["chrome", "--user-data-dir", str(self.expected)],
            ["chrome", f"--user-data-dir={self.expected}", f"--user-data-dir={self.other}"],
            ["chrome", f"--user-data-dir={self.expected}", f"-user-data-dir={self.other}"],
            ["chrome", "--", f"--user-data-dir={self.expected}"],
            ["chrome", f"https://example.com/--user-data-dir={self.expected}"],
            ["chrome", 42], None,
        ):
            with self.subTest(arguments=arguments):
                self.client.call.return_value = {"arguments": arguments}
                with self.assertRaisesRegex(RuntimeError, "cannot verify CDP profile"):
                    cdp.command_launch(self.args("launch"))
        self.launch_mock.assert_not_called()
        self.tabs_mock.assert_not_called()


if __name__ == "__main__":
    unittest.main()
