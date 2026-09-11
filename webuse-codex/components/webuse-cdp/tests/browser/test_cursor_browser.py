"""Opt-in real Chrome tests. Uses only a disposable headless browser and local HTML.

Run: python -B -m unittest discover -s components/webuse-cdp/tests/browser -v
Pillow is needed by the pointer compositor and these pixel assertions.
"""

import io
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import threading
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from test_profile_verification import cdp


class BrowserCursorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from PIL import Image, ImageChops
        cls.Image, cls.ImageChops = Image, ImageChops
        cls.tests_dir = Path(__file__).resolve().parent
        cls.temp = tempfile.TemporaryDirectory(prefix="webuse-cdp-browser-", dir=cls.tests_dir)
        cls.root = Path(cls.temp.name).resolve()
        cls.profile = cls.root / "profile"
        cls.process = None
        cls.browser = None
        cls.http_server = None
        cls.http_thread = None
        cls.addClassCleanup(cls.cleanup)
        # Serve only generated test fixtures on loopback. Do not rely on data:
        # URLs, which are commonly disabled by managed browser installations.
        class FixtureHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                payload = cls.fixture_html.encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)
            def log_message(self, *args):
                pass
        cls.fixture_html = "<!doctype html><html><body></body></html>"
        cls.http_server = ThreadingHTTPServer(("127.0.0.1", 0), FixtureHandler)
        cls.http_thread = threading.Thread(target=cls.http_server.serve_forever, daemon=True)
        cls.http_thread.start()
        cls.fixture_url = f"http://127.0.0.1:{cls.http_server.server_port}/fixture"
        cls.process = subprocess.Popen([
            cdp.find_chrome_executable(), "--headless=new", "--enable-automation",
            "--remote-debugging-address=127.0.0.1", "--remote-debugging-port=0",
            f"--user-data-dir={cls.profile}", "--no-first-run", "--no-default-browser-check",
            "--disable-background-networking", "--disable-component-update", "about:blank",
        ], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
        deadline = time.monotonic() + 20
        port_file = cls.profile / "DevToolsActivePort"
        while not port_file.exists():
            if cls.process.poll() is not None or time.monotonic() >= deadline:
                raise RuntimeError("isolated test Chrome did not start")
            time.sleep(0.1)
        cls.endpoint = "http://127.0.0.1:" + port_file.read_text().splitlines()[0]
        cls.browser = cdp.CDPClient(cdp.get_version(cls.endpoint)["webSocketDebuggerUrl"])

    @classmethod
    def cleanup(cls):
        if cls.browser is not None:
            try:
                cls.browser.call("Browser.close")
            except (RuntimeError, TimeoutError):
                pass
            finally:
                cls.browser.close()
        if cls.process is not None:
            try:
                cls.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                cls.process.terminate()
                cls.process.wait(timeout=10)
        if cls.http_server is not None:
            cls.http_server.shutdown()
            cls.http_server.server_close()
        if cls.http_thread is not None:
            cls.http_thread.join(timeout=5)
        # Recursive cleanup is confined to the exact disposable test directory.
        if cls.root.parent != cls.tests_dir or not cls.root.name.startswith("webuse-cdp-browser-"):
            raise RuntimeError("refusing cleanup outside the test directory")
        for attempt in range(20):
            try:
                cls.temp.cleanup()
                break
            except PermissionError:
                if attempt == 19:
                    raise
                time.sleep(0.1)

    def run_command(self, *argv):
        # Real subprocesses exercise both fresh CDP sessions and CLI persistence.
        result = subprocess.run([
            sys.executable, "-B", "-X", "utf8", str(cdp.Path(cdp.__file__)),
            "--endpoint", self.endpoint, "--user-data-dir", str(self.profile),
            "--no-auto-launch", *argv, "--json",
        ], capture_output=True, text=True, encoding="utf-8", timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return cdp.json.loads(result.stdout)

    def eval(self, target, expression):
        return self.run_command("eval", "--target-id", target, "--expression", expression)["value"]

    def screenshot(self, target, name, *extra):
        path = self.root / name
        result = self.run_command("screenshot", "--target-id", target, "--output", str(path), *extra)
        with self.Image.open(io.BytesIO(path.read_bytes())) as image:
            pixels = image.convert("RGB")
        return result, pixels

    def test_blank_target_protocol_smoke(self):
        """Live CDP handshake, profile checks, UTF-8 stdin and screenshot export."""
        target = self.browser.call("Target.createTarget", {"url": "about:blank"})["targetId"]
        self.assertEqual(self.eval(target, "location.href"), "about:blank")
        result = subprocess.run([
            sys.executable, "-B", "-X", "utf8", str(cdp.Path(cdp.__file__)),
            "--endpoint", self.endpoint, "--user-data-dir", str(self.profile),
            "--no-auto-launch", "eval", "--target-id", target,
            "--expression-stdin", "--json",
        ], input='JSON.stringify({answer: 6 * 7, text: "\u6d4b\u8bd5"})',
            capture_output=True, text=True, encoding="utf-8", timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        value = cdp.json.loads(cdp.json.loads(result.stdout)["value"])
        self.assertEqual(value, {"answer": 42, "text": "\u6d4b\u8bd5"})
        result, image = self.screenshot(target, "blank-protocol.png", "--no-cursor")
        self.assertGreater(image.width, 0)
        self.assertGreater(image.height, 0)
        self.assertFalse(result["cursor"]["drawn"])

    def test_cursor_rendering_and_lifecycle(self):
        html = """<!doctype html><html><body style='margin:0;background:white;height:2000px'>
        <button id='target' style='position:absolute;left:80px;top:70px;width:180px;height:50px'>Target</button>
        <script>window.clicks=0; document.querySelector('button').onclick=()=>window.clicks++;</script>
        </body></html>"""
        type(self).fixture_html = html
        url = self.fixture_url
        target = self.browser.call("Target.createTarget", {"url": url})["targetId"]
        other = self.browser.call("Target.createTarget", {"url": "about:blank"})["targetId"]
        deadline = time.monotonic() + 8
        while True:
            state = self.eval(target, "({url:location.href, body:document.body?.innerText || '', ready:document.readyState, found:!!document.querySelector('#target')})")
            if state['url'] == 'chrome-error://chromewebdata/' and 'organization' in state['body'].lower():
                self.skipTest('Host browser policy blocks the local HTTP fixture; full rendering workflow was not validated')
            if state['found'] or time.monotonic() >= deadline:
                break
            time.sleep(0.1)
        self.run_command("wait-for-selector", "--target-id", target, "--selector", "#target")
        unknown, _ = self.screenshot(target, "unknown.png")
        self.assertEqual(unknown["cursor"]["reason"], "unknown-position")

        moved = self.run_command("move", "--target-id", target, "--x", "240", "--y", "160")
        self.assertEqual(self.eval(target, "window.clicks"), 0)
        self.assertEqual(moved["cursor"]["x"], 240)
        result, marked = self.screenshot(target, "marked.png")
        self.assertTrue(result["cursor"]["drawn"])
        self.assertEqual(result["cursor"]["source"], "cdp")
        _, plain = self.screenshot(target, "plain.png", "--no-cursor")
        bounds = self.ImageChops.difference(marked, plain).getbbox()
        self.assertIsNotNone(bounds)
        self.assertTrue(238 <= bounds[0] <= 242, bounds)
        self.assertTrue(158 <= bounds[1] <= 162, bounds)
        self.assertLessEqual(bounds[2], 277)
        self.assertLessEqual(bounds[3], 209)
        self.assertEqual(self.eval(target, "document.querySelectorAll('[data-webuse-cdp-cursor]').length"), 0)
        self.assertIsNone(self.eval(target, "globalThis.webusePointer"))  # isolated from page JS

        # Another tab must not inherit a known cursor.
        other_result, _ = self.screenshot(other, "other.png")
        self.assertEqual(other_result["cursor"]["reason"], "unknown-position")

        # Selector moves only hover. Clicks update the same state.
        moved = self.run_command("move", "--target-id", target, "--selector", "#target")
        self.assertEqual(self.eval(target, "window.clicks"), 0)
        self.assertEqual(moved["cursor"]["x"], 170)
        self.run_command("click", "--target-id", target, "--selector", "#target")
        self.assertEqual(self.eval(target, "window.clicks"), 1)
        clicked, _ = self.screenshot(target, "clicked.png")
        self.assertEqual(clicked["cursor"]["x"], 170)
        self.assertEqual(clicked["cursor"]["y"], 95)

        # The compositor maps CSS coordinates to the actual screenshot scale.
        args = cdp.build_parser().parse_args([
            "--endpoint", self.endpoint, "--user-data-dir", str(self.profile),
            "--no-auto-launch", "screenshot", "--target-id", target,
        ])
        client, _ = cdp.connect_target(args)
        try:
            client.call("Emulation.setDeviceMetricsOverride", {
                "width": 800, "height": 600, "deviceScaleFactor": 2, "mobile": False,
            })
            self.run_command("move", "--target-id", target, "--x", "240", "--y", "160")
            _, scaled = self.screenshot(target, "scaled.png")
            _, scaled_plain = self.screenshot(target, "scaled-plain.png", "--no-cursor")
            self.assertEqual(scaled.size, (1600, 1200))
            scaled_bounds = self.ImageChops.difference(scaled, scaled_plain).getbbox()
            self.assertTrue(477 <= scaled_bounds[0] <= 483, scaled_bounds)
            self.assertTrue(317 <= scaled_bounds[1] <= 323, scaled_bounds)
            client.call("Emulation.clearDeviceMetricsOverride")

            # A capture failure must not leave any marker DOM behind.
            original_call = client.call
            def failing_capture(method, *params, **kwargs):
                if method == "Page.captureScreenshot":
                    raise RuntimeError("intentional capture failure")
                return original_call(method, *params, **kwargs)
            with patch.object(cdp, "connect_target", return_value=(client, {"id": target})), \
                 patch.object(client, "call", side_effect=failing_capture):
                with self.assertRaisesRegex(RuntimeError, "intentional capture failure"):
                    cdp.command_screenshot(args)
        finally:
            client.close()
        self.assertEqual(self.eval(target, "document.querySelectorAll('[data-webuse-cdp-cursor]').length"), 0)

        # Replacing the document invalidates the old coordinates.
        self.run_command("navigate", "--target-id", target, "--url", "about:blank", "--wait-load")
        reset, _ = self.screenshot(target, "reset.png")
        self.assertEqual(reset["cursor"]["reason"], "unknown-position")


if __name__ == "__main__":
    unittest.main()
