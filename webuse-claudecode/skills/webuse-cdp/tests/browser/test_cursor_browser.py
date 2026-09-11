"""Opt-in real Chrome tests. Uses only a disposable headless browser and local HTML.

Run: python -B -m unittest discover -s skills/webuse-cdp/tests/browser -v
Pillow is needed by the pointer compositor and these pixel assertions.
"""

import io
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.parse
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
        cls.addClassCleanup(cls.cleanup)
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

    def test_cursor_rendering_and_lifecycle(self):
        html = """<!doctype html><html><body style='margin:0;background:white;height:2000px'>
        <button id='target' style='position:absolute;left:80px;top:70px;width:180px;height:50px'>Target</button>
        <script>window.clicks=0; document.querySelector('button').onclick=()=>window.clicks++;</script>
        </body></html>"""
        url = "data:text/html," + urllib.parse.quote(html)
        target = self.browser.call("Target.createTarget", {"url": url})["targetId"]
        other = self.browser.call("Target.createTarget", {"url": "about:blank"})["targetId"]
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
