"""Project-wide UTF-8 and line-ending regression tests."""

import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from test_profile_verification import cdp


ROOT = Path(__file__).resolve().parents[2]


def load_module(name, relative_path):
    path = ROOT / relative_path
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


mem = load_module("webuse_mem_encoding_test", "webuse-mem/scripts/webuse_mem.py")
mouse = load_module("webuse_mouse_encoding_test", "webuse-mouse-control/scripts/webuse_mouse_control.py")
screenshot = load_module("webuse_screenshot_encoding_test", "webuse-screenshot/scripts/webuse_screenshot.py")
typing = load_module("webuse_typing_encoding_test", "webuse-typing/scripts/webuse_typing.py")


class FakeStream:
    def __init__(self):
        self.calls = []

    def reconfigure(self, **kwargs):
        self.calls.append(kwargs)


class EncodingTests(unittest.TestCase):
    def test_all_cli_standard_streams_are_configured_as_utf8(self):
        for module in (cdp, mem, mouse, screenshot, typing):
            with self.subTest(module=module.__name__):
                streams = [FakeStream(), FakeStream(), FakeStream()]
                with patch.object(sys, "stdin", streams[0]), \
                     patch.object(sys, "stdout", streams[1]), \
                     patch.object(sys, "stderr", streams[2]):
                    module.configure_utf8_stdio()
                for stream in streams:
                    self.assertEqual(
                        stream.calls,
                        [{"encoding": "utf-8", "errors": "strict"}],
                    )

    def test_mem_generated_files_are_utf8_without_bom_and_use_lf(self):
        with tempfile.TemporaryDirectory(prefix="webuse-mem-encoding-") as directory:
            mem_path = Path(directory) / "Mem"
            mem.ensure_structure(mem_path, create=True)
            target = mem_path / "中文任务" / "memory.md"
            mem.append_block(target, "中文内容", "编码测试")
            mem.rebuild_content(mem_path)

            for path in mem_path.rglob("*.md"):
                data = path.read_bytes()
                self.assertNotIn(b"\xef\xbb\xbf", data, path)
                self.assertNotIn(b"\r", data, path)
                self.assertIn("中文" if path == target else "#", data.decode("utf-8"))

    def test_mem_rejects_invalid_utf8_instead_of_silently_replacing_it(self):
        with tempfile.TemporaryDirectory(prefix="webuse-mem-invalid-encoding-") as directory:
            path = Path(directory) / "broken.md"
            path.write_bytes(b"# broken\n\xff\n")

            with self.assertRaises(UnicodeDecodeError):
                mem.read_text_file(path)
            with self.assertRaises(UnicodeDecodeError):
                mem.search_file(path, ["broken"], "broken")

    def test_repository_text_files_follow_encoding_policy(self):
        extensions = {".py", ".md", ".txt", ".yaml", ".yml"}
        special_names = {".editorconfig", ".gitattributes"}
        paths = [
            path
            for path in ROOT.rglob("*")
            if path.is_file()
            and (path.suffix.lower() in extensions or path.name in special_names)
        ]
        self.assertTrue(paths)
        for path in paths:
            with self.subTest(path=path.relative_to(ROOT)):
                data = path.read_bytes()
                data.decode("utf-8", errors="strict")
                self.assertNotIn(b"\xef\xbb\xbf", data)
                self.assertNotIn(b"\r", data)
                self.assertTrue(data.endswith(b"\n"))


if __name__ == "__main__":
    unittest.main()
