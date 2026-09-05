"""Opt-in integration test using a temporary, isolated headless browser."""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.parse
import urllib.request


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "webmind.py"
CHROME = os.environ.get("WEBMIND_TEST_CHROME")


@unittest.skipUnless(CHROME, "Set WEBMIND_TEST_CHROME to run the isolated browser test")
class BrowserIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix="webmind-test-")
        cls.addClassCleanup(cls.temp.cleanup)
        cls.root = Path(cls.temp.name)
        profile = cls.root / "profile"
        cls.browser = subprocess.Popen(
            [
                CHROME, "--headless=new", "--remote-debugging-address=127.0.0.1",
                "--remote-debugging-port=0", f"--user-data-dir={profile}",
                "--no-first-run", "--no-default-browser-check",
                "--disable-background-networking", "--disable-sync", "about:blank",
            ],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        cls.addClassCleanup(cls.stop_browser)
        port_file = profile / "DevToolsActivePort"
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        deadline = time.monotonic() + 20
        while time.monotonic() < deadline:
            if cls.browser.poll() is not None:
                raise RuntimeError("The isolated test browser exited before CDP was ready")
            try:
                port = int(port_file.read_text().splitlines()[0])
                cls.endpoint = f"http://127.0.0.1:{port}"
                with opener.open(cls.endpoint + "/json/version", timeout=1) as response:
                    json.load(response)
                return
            except (OSError, ValueError, IndexError):
                time.sleep(0.1)
        raise RuntimeError("The isolated test browser did not expose a CDP endpoint")

    @classmethod
    def stop_browser(cls):
        if cls.browser.poll() is None:
            cls.browser.terminate()
            try:
                cls.browser.wait(timeout=10)
            except subprocess.TimeoutExpired:
                cls.browser.kill()
                cls.browser.wait(timeout=5)

    def cli(self, *args):
        result = subprocess.run(
            [
                sys.executable, "-X", "utf8", str(SCRIPT),
                "--endpoint", self.endpoint, "--no-auto-launch", *args, "--json",
            ],
            capture_output=True, encoding="utf-8", timeout=20,
        )
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["ok"], payload)
        return payload

    def test_read_fill_click_and_capture_page(self):
        self.cli("self-check")
        pages = self.cli("tabs")["tabs"]
        target = next(page["id"] for page in pages if page["type"] == "page")
        html = (
            '<!doctype html><meta charset="utf-8"><title>WebMind test</title>'
            '<input id="query"><button id="submit" '
            'onclick="document.body.dataset.clicked=\'yes\'">Submit</button>'
            '<div id="editor" contenteditable="true"></div>'
        )
        self.cli(
            "navigate", "--target-id", target, "--url",
            "data:text/html;charset=utf-8," + urllib.parse.quote(html), "--wait-load",
        )
        self.cli("wait-for-selector", "--target-id", target, "--selector", "#query", "--visible")
        text = 'WebMind 中文 🌐 "quoted"'
        self.cli("fill", "--target-id", target, "--selector", "#query", "--text", text)
        self.cli("click", "--target-id", target, "--selector", "#submit")
        self.cli("insert-text", "--target-id", target, "--selector", "#editor", "--text", "Draft")
        self.cli("press", "--target-id", target, "--key", "End")
        value = self.cli(
            "eval", "--target-id", target, "--expression",
            '({title:document.title,text:document.querySelector("#query").value,'
            'clicked:document.body.dataset.clicked,editor:document.querySelector("#editor").innerText})',
        )["value"]
        self.assertEqual(value, {"title": "WebMind test", "text": text, "clicked": "yes", "editor": "Draft"})
        screenshot = self.root / "viewport.png"
        self.cli("screenshot", "--target-id", target, "--output", str(screenshot))
        self.assertTrue(screenshot.read_bytes().startswith(b"\x89PNG\r\n\x1a\n"))


if __name__ == "__main__":
    unittest.main()
