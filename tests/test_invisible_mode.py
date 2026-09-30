"""Browser-mode regression checks with no live browser or user Profile access."""
from __future__ import annotations

from contextlib import ExitStack
import importlib.util
import io
import json
from pathlib import Path
import unittest
from unittest.mock import Mock, patch


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
        self.stack.enter_context(patch.object(cdp.platform, "platform", return_value="Windows-test"))
        self.stack.enter_context(patch.object(cdp, "load_browser_configuration", return_value=self.config))
        self.process = self.stack.enter_context(patch.object(cdp.subprocess, "Popen"))
        self.process.return_value.pid = 1234
        # Allow these isolated checks to run on non-Windows development hosts too.
        for flag in ("CREATE_NEW_PROCESS_GROUP", "DETACHED_PROCESS"):
            self.stack.enter_context(patch.object(cdp.subprocess, flag, 0, create=True))
        self.stack.enter_context(patch.object(cdp, "find_chrome_executable", return_value="chrome.exe"))
        self.version = {"webSocketDebuggerUrl": "ws://127.0.0.1:9042/devtools/browser/test"}
        self.client = Mock()
        self.stack.enter_context(patch.object(cdp, "CDPClient", return_value=self.client))
        self.get_version = self.stack.enter_context(patch.object(cdp, "get_version", return_value=self.version))
        self.get_tabs = self.stack.enter_context(patch.object(cdp, "get_tabs", return_value=[]))

    def args(self, invisible=None, command=None):
        flags = [] if invisible is None else ["--invisible-mode" if invisible else "--visible-mode"]
        argv = flags + (command or ["launch"])
        return cdp.build_parser().parse_args(argv)

    def report_browser(self, invisible=False, profile=None):
        arguments = ["chrome.exe", f"--user-data-dir={profile or self.profile}"]
        if invisible:
            arguments.append("--headless")
        self.client.call.return_value = {"arguments": arguments}
        return arguments

    def test_default_launch_is_invisible(self):
        cdp.launch_chrome(self.args())
        command = self.process.call_args.args[0]
        self.assertIn("--headless", command)
        self.assertIn("--window-size=1280,800", command)
        self.assertIn("--enable-automation", command)
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

    def test_visible_choice_does_not_carry_to_next_invocation(self):
        cdp.launch_chrome(self.args(False))
        self.assertNotIn("--headless", self.process.call_args.args[0])
        cdp.launch_chrome(self.args())
        self.assertIn("--headless", self.process.call_args.args[0])
        self.assertNotIn("invisible_mode", self.config)

    def test_new_tab_background_flag_does_not_select_browser_mode(self):
        args = self.args(command=["new-tab", "--background"])
        self.assertTrue(args.background)
        self.assertEqual(cdp.requested_browser_mode(args), "invisible")

    def test_invisible_mode_rejects_new_window_before_launch(self):
        with self.assertRaisesRegex(ValueError, "--new-window"):
            cdp.command_launch(self.args(True, ["launch", "--new-window"]))
        self.process.assert_not_called()
        self.get_version.assert_not_called()

    def test_actual_mode_uses_switches_not_urls_or_arguments_after_terminator(self):
        for switch in ("--headless", "--headless=new", "-HEADLESS", "/headless"):
            with self.subTest(switch=switch):
                self.assertEqual(cdp.browser_mode_from_arguments(["chrome.exe", switch]), "invisible")
        for arguments in (
            ["chrome.exe", "https://example.com/--headless"],
            ["chrome.exe", "--", "--headless"],
            ["chrome.exe", "--headless-other"],
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

    def test_both_mode_mismatches_reuse_existing_browser_with_notice(self):
        for requested in (False, True):
            with self.subTest(requested=requested):
                self.report_browser(not requested)
                args = self.args(requested)
                result = cdp.ensure_endpoint(args)
                self.assertIsNone(result["launch"])
                self.assertTrue(result["browser_reused"])
                self.assertEqual(result["browser_mode"], "visible" if requested else "invisible")
                self.assertEqual(cdp.requested_browser_mode(args), "invisible" if requested else "visible")
                mode = "可见" if requested else "不可见"
                self.assertEqual(cdp.browser_mode_notice(args),
                                 f"已有浏览器正在使用{mode}模式，Agent将继续使用已有浏览器工作；"
                                 "如果想要切换，请按下ESC阻止Agent。")
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

    def test_windows_command_line_fallback_checks_mode(self):
        arguments = self.report_browser(True)
        self.client.call.side_effect = [RuntimeError("not available"), {"commandLine": "test command"}]
        with patch.object(cdp, "split_browser_command_line", return_value=arguments) as split:
            self.assertEqual(cdp.ensure_endpoint(self.args(True))["browser_mode"], "invisible")
            split.assert_called_once_with("test command")

    def test_auto_launch_honors_invisible_choice_and_verifies_result(self):
        self.get_version.side_effect = [OSError("not running"), self.version]
        self.report_browser(True)
        with patch.object(cdp, "wait_for_endpoint", return_value=True):
            result = cdp.ensure_endpoint(self.args(True, ["tabs"]))
        self.assertIn("--headless", self.process.call_args.args[0])
        self.assertEqual(result["browser_mode"], "invisible")

    def test_newly_launched_browser_reports_actual_mode_without_retry(self):
        self.get_version.side_effect = [OSError("not running"), self.version]
        self.report_browser(False)
        with patch.object(cdp, "wait_for_endpoint", return_value=True):
            args = self.args(True)
            result = cdp.ensure_endpoint(args)
        self.assertEqual(result["browser_mode"], "visible")
        self.assertFalse(result["browser_reused"])
        self.assertIsNone(cdp.browser_mode_notice(args))
        self.process.assert_called_once()

    def test_no_auto_launch_is_preserved(self):
        self.get_version.side_effect = OSError("not running")
        args = cdp.build_parser().parse_args(["--invisible-mode", "--no-auto-launch", "tabs"])
        with self.assertRaises(OSError):
            cdp.ensure_endpoint(args)
        self.process.assert_not_called()

    def test_self_check_accepts_existing_mode_without_launching(self):
        self.report_browser(False)
        args = self.args(command=["self-check"])
        result = cdp.command_self_check(args)
        self.assertTrue(result["ok"])
        self.assertEqual(args.browser_mode, "visible")
        self.assertIn("已有浏览器正在使用可见模式", cdp.browser_mode_notice(args))
        self.get_tabs.assert_called_once()
        self.process.assert_not_called()

    def test_page_actions_continue_in_existing_mode(self):
        arguments = self.report_browser(False)
        self.get_tabs.return_value = [{"id": "test", "type": "page",
                                      "webSocketDebuggerUrl": "ws://127.0.0.1:9042/test"}]
        def reply(method, *unused_args, **unused_kwargs):
            if method == "Browser.getBrowserCommandLine":
                return {"arguments": arguments}
            if method == "Runtime.evaluate":
                return {"result": {"type": "string", "value": "Test page"}}
            return {}
        self.client.call.side_effect = reply
        args = self.args(command=["eval", "--target-id", "test", "--expression", "document.title"])
        result = cdp.command_eval(args)
        self.assertTrue(result["ok"])
        self.assertEqual(result["value"], "Test page")
        self.assertEqual(args.browser_mode, "visible")
        self.process.assert_not_called()
        self.assertTrue(any(call.args[0] == "Runtime.evaluate" for call in self.client.call.call_args_list))

    def test_cli_reports_verified_mode(self):
        self.report_browser(True)
        with patch.object(cdp.sys, "argv", [str(SCRIPT), "tabs", "--json"]), \
                patch.object(cdp.platform, "system", return_value="Windows"), \
                patch.object(cdp, "configure_utf8_stdio"), patch("sys.stdout", new_callable=io.StringIO) as output:
            self.assertEqual(cdp.main(), 0)
            result = json.loads(output.getvalue())
        self.assertEqual(result["browser_mode"], "invisible")
        self.assertEqual(result["requested_browser_mode"], "invisible")


    def test_visible_launch_allows_new_window_without_headless_flags(self):
        result = cdp.launch_chrome(self.args(False, ["launch", "--new-window"]))
        command = self.process.call_args.args[0]
        self.assertNotIn("--headless", command)
        self.assertNotIn("--window-size=1280,800", command)
        self.assertIn("--new-window", command)
        self.assertEqual(result["requested_browser_mode"], "visible")

    def test_default_mode_rejects_new_window_before_launch(self):
        with self.assertRaisesRegex(ValueError, "--visible-mode"):
            cdp.command_launch(self.args(command=["launch", "--new-window"]))
        self.process.assert_not_called()
        self.get_version.assert_not_called()

    def test_conflicting_mode_flags_are_rejected_in_both_orders(self):
        for flags in (["--visible-mode", "--invisible-mode"], ["--invisible-mode", "--visible-mode"]):
            with self.subTest(flags=flags), patch("sys.stderr", new_callable=io.StringIO):
                with self.assertRaises(SystemExit) as error:
                    cdp.build_parser().parse_args([*flags, "launch"])
                self.assertEqual(error.exception.code, 2)
        self.process.assert_not_called()

    def test_default_auto_launch_is_invisible_and_verifies_result(self):
        self.get_version.side_effect = [OSError("not running"), self.version]
        self.report_browser(True)
        with patch.object(cdp, "wait_for_endpoint", return_value=True):
            result = cdp.ensure_endpoint(self.args(command=["tabs"]))
        self.assertIn("--headless", self.process.call_args.args[0])
        self.assertEqual(result["browser_mode"], "invisible")

    def test_visible_auto_launch_stays_visible(self):
        self.get_version.side_effect = [OSError("not running"), self.version]
        self.report_browser(False)
        with patch.object(cdp, "wait_for_endpoint", return_value=True):
            result = cdp.ensure_endpoint(self.args(False, ["tabs"]))
        self.assertNotIn("--headless", self.process.call_args.args[0])
        self.assertEqual(result["browser_mode"], "visible")

    def test_default_reuses_existing_invisible_browser(self):
        self.report_browser(True)
        result = cdp.ensure_endpoint(self.args())
        self.assertIsNone(result["launch"])
        self.assertEqual(result["browser_mode"], "invisible")
        self.process.assert_not_called()

    def test_default_mode_still_verifies_profile(self):
        self.report_browser(True, self.profile.parent / "unrelated-profile")
        with self.assertRaisesRegex(RuntimeError, "profile mismatch"):
            cdp.ensure_endpoint(self.args())
        self.process.assert_not_called()

    def test_no_auto_launch_is_preserved_with_default_mode(self):
        self.get_version.side_effect = OSError("not running")
        args = cdp.build_parser().parse_args(["--no-auto-launch", "tabs"])
        with self.assertRaises(OSError):
            cdp.ensure_endpoint(args)
        self.process.assert_not_called()


    def test_cli_json_reports_actual_mode_and_notice_on_reuse(self):
        for invisible in (False, True):
            with self.subTest(invisible=invisible):
                self.report_browser(invisible)
                flags = ["--visible-mode"] if invisible else []
                with patch.object(cdp.sys, "argv", [str(SCRIPT), *flags, "tabs", "--json"]), \
                        patch.object(cdp.platform, "system", return_value="Windows"), \
                        patch.object(cdp, "configure_utf8_stdio", create=True), \
                        patch("sys.stdout", new_callable=io.StringIO) as output:
                    self.assertEqual(cdp.main(), 0)
                    result = json.loads(output.getvalue())
                self.assertEqual(result["browser_mode"], "invisible" if invisible else "visible")
                self.assertEqual(result["requested_browser_mode"], "visible" if invisible else "invisible")
                self.assertTrue(result["browser_reused"])
                mode = "不可见" if invisible else "可见"
                self.assertIn(f"已有浏览器正在使用{mode}模式", result["browser_mode_notice"])
                self.assertIn("按下ESC阻止Agent", result["browser_mode_notice"])
        self.process.assert_not_called()

    def test_cli_text_prints_reuse_notice(self):
        self.report_browser(False)
        with patch.object(cdp.sys, "argv", [str(SCRIPT), "tabs"]), \
                patch.object(cdp.platform, "system", return_value="Windows"), \
                patch.object(cdp, "configure_utf8_stdio", create=True), \
                patch("sys.stdout", new_callable=io.StringIO) as output:
            self.assertEqual(cdp.main(), 0)
        self.assertIn("已有浏览器正在使用可见模式，Agent将继续使用已有浏览器工作", output.getvalue())
        self.process.assert_not_called()

    def test_self_check_profile_mismatch_still_fails_without_reuse_notice(self):
        self.report_browser(False, self.profile.parent / "unrelated-profile")
        args = self.args(command=["self-check"])
        result = cdp.command_self_check(args)
        self.assertFalse(result["ok"])
        self.assertIn("profile mismatch", result["error"])
        self.assertIsNone(cdp.browser_mode_notice(args))
        self.get_tabs.assert_not_called()
        self.process.assert_not_called()

    def test_matching_mode_also_announces_reuse(self):
        for invisible in (False, True):
            with self.subTest(invisible=invisible):
                self.report_browser(invisible)
                args = self.args(invisible)
                cdp.ensure_endpoint(args)
                self.assertIsNotNone(cdp.browser_mode_notice(args))
        self.process.assert_not_called()

    def test_fresh_launch_has_no_existing_browser_notice(self):
        self.get_version.side_effect = [OSError("not running"), self.version]
        self.report_browser(True)
        args = self.args()
        with patch.object(cdp, "wait_for_endpoint", return_value=True):
            result = cdp.ensure_endpoint(args)
        self.assertFalse(result["browser_reused"])
        self.assertIsNone(cdp.browser_mode_notice(args))
        self.assertEqual(result["browser_mode"], "invisible")


    def test_failed_cli_does_not_announce_continuation(self):
        self.report_browser(False)
        self.get_tabs.side_effect = OSError("tab listing failed")
        with patch.object(cdp.sys, "argv", [str(SCRIPT), "self-check", "--json"]), \
                patch.object(cdp.platform, "system", return_value="Windows"), \
                patch.object(cdp, "configure_utf8_stdio", create=True), \
                patch("sys.stdout", new_callable=io.StringIO) as output:
            self.assertEqual(cdp.main(), 1)
            result = json.loads(output.getvalue())
        self.assertFalse(result["ok"])
        self.assertIn("tab listing failed", result["error"])
        self.assertNotIn("browser_mode_notice", result)
        self.process.assert_not_called()


if __name__ == "__main__":
    unittest.main()
