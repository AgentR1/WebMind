"""Opt-in end-to-end tasks on deterministic local sites and an owned browser.

No real account, external website, or user's existing browser is involved.
"""

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import socket
import threading
import unittest
import urllib.request

from test_browser_integration import CHROME, IsolatedBrowserTestCase


FIXTURES = Path(__file__).resolve().parent / "fixtures"


class ScenarioHandler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_GET(self):
        path = self.path.split("?", 1)[0]
        headers = {}
        status = 200
        if path in {"/article.html", "/dynamic.html", "/blocked.html", "/fallback.html",
                    "/input-guards.html", "/reading-edge-cases.html"}:
            body = (FIXTURES / path.lstrip("/")).read_bytes()
        elif path == "/auth/login":
            headers["Set-Cookie"] = "webmind_test_session=authenticated; Path=/; HttpOnly; SameSite=Lax"
            body = b'<main><h1>Local test login complete</h1></main>'
        elif path == "/auth/account":
            if "webmind_test_session=authenticated" in self.headers.get("Cookie", ""):
                body = b'<main id="account"><h1>Fixture account</h1><p>Authenticated test content</p></main>'
            else:
                body = b'<main id="anonymous">Sign in required</main>'
        elif path == "/stall.html":
            body = b'<main>Waiting for image</main><img src="/slow-resource">'
        elif path == "/slow-resource":
            self.server.release_slow.wait(timeout=10)
            body = b"not-an-image"
        else:
            status = 404
            body = b"Not found"
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        for key, value in headers.items():
            self.send_header(key, value)
        self.end_headers()
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            pass


@unittest.skipUnless(CHROME, "Set WEBMIND_TEST_CHROME to run local browser scenarios")
class BrowserTaskScenarios(IsolatedBrowserTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), ScenarioHandler)
        cls.server.daemon_threads = True
        cls.server.release_slow = threading.Event()
        cls.server_thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.server_thread.start()
        cls.addClassCleanup(cls.stop_server)
        cls.site = f"http://127.0.0.1:{cls.server.server_port}"
        cls.opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

    @classmethod
    def stop_server(cls):
        cls.server.release_slow.set()
        cls.server.shutdown()
        cls.server.server_close()
        cls.server_thread.join(timeout=5)

    def setUp(self):
        pages = [page for page in self.cli("tabs")["tabs"] if page["type"] == "page"]
        self.target = pages[0]["id"]

    def navigate(self, path):
        return self.cli("navigate", "--target-id", self.target, "--url", self.site + path, "--wait-load")

    def read_page(self, *args):
        payload = self.cli("read-page", "--target-id", self.target, *args)
        self.assertEqual(payload["action"], "read-page")
        self.assertEqual(payload["target"]["id"], self.target)
        return payload["page"]

    def test_read_article_preserves_chinese_structure_and_filters_noise(self):
        self.navigate("/article.html")
        page = self.read_page()
        self.assertEqual(page["title"], "WebMind 中文阅读样例")
        self.assertEqual(page["url"], self.site + "/article.html")
        self.assertEqual(page["lang"], "zh-CN")
        self.assertIn("第一段，包含中文、标点和 emoji 🌐", page["text"])
        self.assertIn("第二段解释如何从网页获取信息", page["text"])
        self.assertLess(page["text"].index("第一段"), page["text"].index("第二段"))
        self.assertNotIn("NOISE", page["text"])
        self.assertIn({"level": 1, "text": "读懂真实网页"}, page["headings"])
        self.assertIn({"level": 2, "text": "可验证的阅读结果"}, page["headings"])
        self.assertIn({"text": "参考资料", "url": self.site + "/reference"}, page["links"])
        self.assertEqual(sum(link["url"] == self.site + "/reference" for link in page["links"]), 1)
        self.assertIn({"text": "原始来源", "url": "https://example.org/source"}, page["links"])
        self.assertFalse(any(link["url"].startswith("javascript:") for link in page["links"]))
        self.assertFalse(any("HIDDEN_LINK" in link["text"] for link in page["links"]))
        self.assertTrue(page["extraction"]["method"])
        self.assertIn("selector", page["extraction"])
        self.assertFalse(page["truncated"]["text"])
        self.assertFalse(page["truncated"]["links"])
        self.assertEqual(self.cli("eval", "--target-id", self.target, "--expression",
                                  "document.querySelector('#hidden-text').textContent")["value"],
                         "HIDDEN_ATTRIBUTE_NOISE", "Reading must not remove nodes from the actual page")

    def test_unstructured_page_uses_body_fallback(self):
        self.navigate("/fallback.html")
        page = self.read_page()
        self.assertIn("Visible text without a semantic article container", page["text"])
        self.assertIn("Read an inline formatted sentence.", page["text"])
        self.assertNotIn("NOISE", page["text"])
        self.assertEqual(page["extraction"]["selector"], "body")

    def test_long_articles_inside_navigation_or_aside_do_not_replace_main_content(self):
        self.navigate("/reading-edge-cases.html")
        page = self.read_page()
        self.assertIn("PRIMARY_ARTICLE_TEXT", page["text"])
        self.assertNotIn("NAV_ARTICLE_NOISE", page["text"])
        self.assertNotIn("ASIDE_ARTICLE_NOISE", page["text"])

    def test_closed_details_only_exposes_summary_until_opened(self):
        self.navigate("/reading-edge-cases.html")
        page = self.read_page("--selector", "#primary")
        self.assertIn("折叠摘要仍应可读", page["text"])
        self.assertNotIn("COLLAPSED_PRIVATE_TEXT", page["text"])
        self.assertFalse(any(link["url"] == self.site + "/detail-link" for link in page["links"]))
        self.cli_error("read-page", "--target-id", self.target, "--selector", "#collapsed-content")
        self.cli("eval", "--target-id", self.target, "--expression", "document.querySelector('#folded').open = true")
        opened = self.read_page("--selector", "#collapsed-content")
        self.assertIn("COLLAPSED_PRIVATE_TEXT", opened["text"])
        self.assertIn({"text": "折叠正文链接", "url": self.site + "/detail-link"}, opened["links"])

    def test_explicit_selector_and_output_limits(self):
        self.navigate("/article.html")
        page = self.read_page("--selector", "#specific")
        self.assertIn("只读取这一段", page["text"])
        self.assertNotIn("第一段", page["text"])
        self.assertEqual(page["extraction"]["selector"], "#specific")
        self.assertEqual(page["links"], [{"text": "指定链接", "url": self.site + "/specific-link"}])
        limited = self.read_page("--selector", "#story", "--max-chars", "28", "--max-links", "1")
        self.assertLessEqual(len(limited["text"]), 28)
        self.assertEqual(len(limited["links"]), 1)
        self.assertTrue(limited["truncated"]["text"])
        self.assertTrue(limited["truncated"]["links"])
        no_links = self.read_page("--selector", "#story", "--max-links", "0")
        self.assertEqual(no_links["links"], [])
        self.assertTrue(no_links["truncated"]["links"])

    def test_missing_explicit_selector_is_an_error(self):
        self.navigate("/article.html")
        self.cli_error("read-page", "--target-id", self.target, "--selector", "#does-not-exist")

    def test_ambiguous_or_hidden_explicit_selector_is_an_error(self):
        self.navigate("/article.html")
        for selector in ("p", "#hidden-text"):
            with self.subTest(selector=selector):
                self.cli_error("read-page", "--target-id", self.target, "--selector", selector)

    def test_read_page_waits_for_dynamic_content(self):
        self.navigate("/dynamic.html")
        self.cli("eval", "--target-id", self.target, "--expression", "window.loadArticle()")
        page = self.read_page("--wait-selector", "#ready", "--timeout", "5")
        self.assertIn("动态渲染完成后的正文", page["text"])
        self.assertNotIn("正在加载", page["text"])

    def test_read_page_wait_timeout_is_an_error(self):
        self.navigate("/dynamic.html")
        self.cli_error("read-page", "--target-id", self.target,
                       "--wait-selector", "#never-created", "--timeout", "0.25")

    def test_multiple_tabs_require_an_unambiguous_target(self):
        self.navigate("/article.html")
        request = urllib.request.Request(self.endpoint + "/json/new?about:blank", method="PUT")
        with self.opener.open(request, timeout=5) as response:
            second = json.load(response)
        try:
            self.cli("navigate", "--target-id", second["id"], "--url", self.site + "/article.html", "--wait-load")
            self.cli_error("eval", "--expression", "document.title")
            self.cli_error("eval", "--url-contains", "/article.html", "--expression", "document.title")
            self.cli_error("eval", "--title-contains", "WebMind", "--expression", "document.title")
            self.assertEqual(self.cli("eval", "--target-id", second["id"], "--expression", "document.title")["value"],
                             "WebMind 中文阅读样例")
        finally:
            with self.opener.open(self.endpoint + "/json/close/" + second["id"], timeout=5) as response:
                response.read()

    def test_test_cookie_login_survives_separate_cli_processes(self):
        self.navigate("/auth/account")
        self.assertEqual(self.cli("eval", "--target-id", self.target, "--expression",
                                  "document.querySelector('#anonymous').textContent")["value"], "Sign in required")
        self.navigate("/auth/login")
        self.navigate("/auth/account")
        page = self.read_page("--selector", "#account")
        self.assertIn("Authenticated test content", page["text"])
        self.assertNotIn("Sign in required", page["text"])

    def test_failed_navigation_can_recover(self):
        with socket.socket() as unavailable:
            unavailable.bind(("127.0.0.1", 0))
            failed_url = f"http://127.0.0.1:{unavailable.getsockname()[1]}/unavailable"
            payload = self.cli_error("navigate", "--target-id", self.target, "--url", failed_url,
                                     "--wait-load", "--timeout", "1")
            self.assertEqual(payload["action"], "navigate")
        self.navigate("/article.html")
        self.assertEqual(self.cli("eval", "--target-id", self.target, "--expression", "document.title")["value"],
                         "WebMind 中文阅读样例")

    def test_wait_load_timeout_is_an_error_and_can_recover(self):
        self.server.release_slow.clear()
        try:
            payload = self.cli_error("navigate", "--target-id", self.target, "--url", self.site + "/stall.html",
                                     "--wait-load", "--timeout", "0.25")
            self.assertEqual(payload["action"], "navigate")
            self.assertFalse(payload["load_event_seen"])
        finally:
            self.server.release_slow.set()
        self.navigate("/article.html")

    def test_covered_button_is_refused_without_firing_handler(self):
        self.navigate("/blocked.html")
        self.cli_error("click", "--target-id", self.target, "--selector", "#covered")
        value = self.cli("eval", "--target-id", self.target, "--expression", "document.body.dataset.clicked || null")["value"]
        self.assertIsNone(value)
        self.cli("eval", "--target-id", self.target, "--expression", "document.querySelector('#overlay').remove()")
        self.cli("click", "--target-id", self.target, "--selector", "#covered")
        self.assertEqual(self.cli("eval", "--target-id", self.target, "--expression", "document.body.dataset.clicked")["value"], "yes")

    def test_insert_text_rejects_noneditable_targets_without_changing_old_focus(self):
        self.navigate("/input-guards.html")
        for selector in ("#disabled", "#readonly", "#plain"):
            with self.subTest(selector=selector):
                self.cli("eval", "--target-id", self.target, "--expression", "document.querySelector('#focused').focus()")
                self.cli_error("insert-text", "--target-id", self.target, "--selector", selector, "--text", "UNEXPECTED")
                values = self.cli("eval", "--target-id", self.target, "--expression",
                                  "({focused:document.querySelector('#focused').value,"
                                  "disabled:document.querySelector('#disabled').value,"
                                  "readonly:document.querySelector('#readonly').value,"
                                  "plain:document.querySelector('#plain').textContent})")["value"]
                self.assertEqual(values, {"focused": "Keep this text", "disabled": "disabled value",
                                          "readonly": "readonly value", "plain": "Not editable"})
        self.cli("insert-text", "--target-id", self.target, "--selector", "#editable", "--text", "Expected 中文")
        self.assertEqual(self.cli("eval", "--target-id", self.target, "--expression",
                                  "document.querySelector('#editable').value")["value"], "Expected 中文")

    def test_fill_reports_when_input_handler_rewrites_the_requested_value(self):
        self.navigate("/input-guards.html")
        self.cli_error("fill", "--target-id", self.target, "--selector", "#normalized", "--text", "Mixed case")
        self.assertEqual(self.cli("eval", "--target-id", self.target, "--expression",
                                  "document.querySelector('#normalized').value")["value"], "MIXED CASE")


if __name__ == "__main__":
    unittest.main()
