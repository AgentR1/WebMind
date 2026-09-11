"""Code-only regression tests for portable memory paths and names."""

import importlib.util
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "webuse_mem.py"
SPEC = importlib.util.spec_from_file_location("webuse_mem_test", SCRIPT)
mem = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = mem
SPEC.loader.exec_module(mem)


class MemoryTests(unittest.TestCase):
    def test_data_dir_override_controls_default_mem_path(self):
        with tempfile.TemporaryDirectory() as directory, \
             patch.dict(os.environ, {"WEBUSE_DATA_DIR": directory}):
            path, warnings = mem.normalize_mem_path(None)
        self.assertEqual(path, (Path(directory) / "Mem").resolve())
        self.assertEqual(warnings, [])

    def test_windows_reserved_names_are_made_portable(self):
        self.assertEqual(mem.safe_task_name("CON"), "CON_")
        self.assertEqual(mem.safe_file_name("LPT1.md"), "_LPT1.md")

    def test_utf8_search_limit_does_not_split_last_code_point(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "large.md"
            prefix = "a" * (mem.MAX_SEARCH_BYTES - 1)
            path.write_text(prefix + "中", encoding="utf-8")
            result = mem.search_file(path, ["a"], "a")
        self.assertIsNotNone(result)

    def test_content_index_does_not_persist_machine_specific_path(self):
        with tempfile.TemporaryDirectory() as directory:
            mem_path = Path(directory) / "Mem"
            mem.ensure_structure(mem_path, create=True)
            content = (mem_path / "content.md").read_text(encoding="utf-8")

        self.assertIn("- path: `Mem/`", content)
        self.assertNotIn(str(mem_path), content)


if __name__ == "__main__":
    unittest.main()
