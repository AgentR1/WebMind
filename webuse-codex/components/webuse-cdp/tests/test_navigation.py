"""Regression tests for Page.navigate failures."""

import contextlib
import io
import json
import sys
import unittest
from unittest.mock import Mock, patch

from test_profile_verification import cdp


class NavigationTests(unittest.TestCase):
    def args(self, *argv):
        return cdp.build_parser().parse_args(list(argv))

    def navigation_client(self, result):
        client = Mock()
        client.call.return_value = result
        tab = {
            "id": "tab-1",
            "title": "Before navigation",
            "url": "about:blank",
            "type": "page",
        }
        return client, tab

    def test_error_text_returns_structured_failure(self):
        client, tab = self.navigation_client(
            {"frameId": "frame-1", "errorText": "net::ERR_NAME_NOT_RESOLVED"}
        )
        args = self.args(
            "navigate", "--url", "https://not-found.invalid", "--wait-load", "--timeout", "5"
        )

        with patch.object(cdp, "connect_target", return_value=(client, tab)):
            result = cdp.command_navigate(args)

        self.assertFalse(result["ok"])
        self.assertEqual(result["action"], "navigate")
        self.assertEqual(result["result"]["errorText"], "net::ERR_NAME_NOT_RESOLVED")
        self.assertIn("net::ERR_NAME_NOT_RESOLVED", result["error"])
        self.assertFalse(result["load_event_seen"])
        client.call.assert_called_once_with(
            "Page.navigate", {"url": "https://not-found.invalid"}
        )
        client.drain_events.assert_not_called()
        client.close.assert_called_once()

    def test_empty_error_text_remains_successful(self):
        client, tab = self.navigation_client({"frameId": "frame-1", "errorText": ""})
        args = self.args("navigate", "--url", "https://example.com")

        with patch.object(cdp, "connect_target", return_value=(client, tab)):
            result = cdp.command_navigate(args)

        self.assertTrue(result["ok"])
        self.assertNotIn("error", result)
        client.close.assert_called_once()

    def test_cli_error_text_emits_false_and_nonzero_exit(self):
        client, tab = self.navigation_client(
            {"frameId": "frame-1", "errorText": "net::ERR_CONNECTION_REFUSED"}
        )
        stdout = io.StringIO()
        argv = [
            str(cdp.Path(cdp.__file__)),
            "navigate",
            "--url",
            "http://127.0.0.1:1",
            "--json",
        ]

        with patch.object(cdp, "connect_target", return_value=(client, tab)), \
             patch.object(sys, "argv", argv), \
             contextlib.redirect_stdout(stdout):
            exit_code = cdp.main()

        payload = json.loads(stdout.getvalue())
        self.assertEqual(exit_code, 1)
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["result"]["errorText"], "net::ERR_CONNECTION_REFUSED")

    def test_stdin_url_is_used_but_redacted_from_result(self):
        client, tab = self.navigation_client({"frameId": "frame-1"})
        args = self.args("navigate", "--url-stdin")

        with patch.object(cdp, "connect_target", return_value=(client, tab)), \
             patch.object(sys, "stdin", io.StringIO("https://example.com/private\n")):
            result = cdp.command_navigate(args)

        client.call.assert_called_once_with(
            "Page.navigate", {"url": "https://example.com/private"}
        )
        self.assertEqual(result["url"], "<provided via stdin>")

    def test_fill_script_does_not_echo_inserted_value(self):
        script = cdp.fill_script("input", "private-but-non-secret")
        self.assertNotIn("value:el.value", script)


if __name__ == "__main__":
    unittest.main()
