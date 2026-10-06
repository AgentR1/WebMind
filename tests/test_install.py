"""Exercise installation with disposable files, without pip or user settings."""

import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import unittest
import uuid
from unittest.mock import patch


REPO = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("_webmind_installer", REPO / "scripts/install.py")
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


class InstallTests(unittest.TestCase):
    def setUp(self):
        self.root = REPO / (".tmp-install-test-" + uuid.uuid4().hex)
        self.root.mkdir()
        self.root = self.root.resolve()
        self.assertEqual(self.root.parent, REPO.resolve())
        self.assertTrue(self.root.name.startswith(".tmp-install-test-"))
        self.addCleanup(shutil.rmtree, self.root, onerror=installer.retry_readonly_cleanup)
        self.source = self.root / "Desktop" / "下载 WebMind"
        shutil.copytree(REPO, self.source, ignore=installer.ignore_runtime)
        self.config = self.root / "Claude config"
        self.target = self.config / "skills" / installer.PLUGIN_NAME
        self.environment = patch.dict(os.environ, {
            "CLAUDE_CONFIG_DIR": str(self.config),
            "WEBMIND_DATA_DIR": str(self.root / "runtime"),
        })
        self.environment.start()
        self.addCleanup(self.environment.stop)

    def install(self, prepare=None):
        return installer.install_plugin(self.source, self.target, prepare)

    def test_default_target_uses_claude_configuration_root(self):
        self.assertEqual(installer.default_target(), self.target)
        with patch.dict(os.environ, {"CLAUDE_CONFIG_DIR": ""}):
            self.assertEqual(installer.default_target(), Path.home() / ".claude/skills/webmind-claudecode")

    def test_complete_copy_is_independent_and_excludes_private_runtime(self):
        for name in (".git", ".venv", "work-1-mem", "work-1-mem-Profile"):
            (self.source / name).mkdir()
            (self.source / name / "private.txt").write_text("private", encoding="utf-8")
        for name in (".env", "screen.png", "secrets.key", str(installer.MEM_POINTER)):
            (self.source / name).write_text("private", encoding="utf-8")
        self.install()
        for name in installer.SKILLS:
            self.assertTrue((self.target / "skills" / name / "SKILL.md").is_file())
        for name in (".git", ".venv", "work-1-mem", "work-1-mem-Profile", ".env",
                     "screen.png", "secrets.key", str(installer.MEM_POINTER)):
            self.assertFalse((self.target / name).exists(), name)
        self.assertNotEqual((self.target / "scripts/webmind.py").stat().st_ino,
                            (self.source / "scripts/webmind.py").stat().st_ino)
        self.assertEqual(installer.read_owner(self.target)["platform"], installer.NATIVE_PLATFORM)

    def test_update_preserves_destination_mem_pointer_and_backs_up_outside_skills(self):
        self.install()
        pointer = self.target / installer.MEM_POINTER
        selected = b'{"schema": 1, "mem_path": "external-user-choice"}\n'
        pointer.write_bytes(selected)
        (self.source / installer.MEM_POINTER).write_text("different source choice", encoding="utf-8")
        (self.source / "README.md").write_text("updated public instructions", encoding="utf-8")
        report = self.install()
        backup = Path(report["backup"])
        self.assertEqual(pointer.read_bytes(), selected)
        self.assertEqual((backup / installer.MEM_POINTER).read_bytes(), selected)
        self.assertFalse(backup.is_relative_to(self.target.parent))
        self.assertEqual((self.target / "README.md").read_text(encoding="utf-8"), "updated public instructions")

    def test_unknown_target_is_untouched(self):
        self.target.mkdir(parents=True)
        (self.target / "mine.txt").write_text("keep", encoding="utf-8")
        with self.assertRaisesRegex(RuntimeError, "unrecognized"):
            self.install()
        self.assertEqual([p.name for p in self.target.iterdir()], ["mine.txt"])

    def test_different_platform_marker_is_not_overwritten(self):
        self.install()
        marker = self.target / installer.MARKER
        owner = json.loads(marker.read_text(encoding="utf-8"))
        owner["platform"] = "Other platform"
        marker.write_text(json.dumps(owner), encoding="utf-8")
        with self.assertRaisesRegex(RuntimeError, "different-platform"):
            self.install()
        self.assertEqual(json.loads(marker.read_text(encoding="utf-8"))["platform"], "Other platform")

    def test_incomplete_sixth_skill_fails_before_creating_destination(self):
        (self.source / "skills/webmind-wait/SKILL.md").unlink()
        with self.assertRaisesRegex(RuntimeError, "Incomplete"):
            self.install()
        self.assertFalse(self.config.exists())

    def test_source_and_target_cannot_contain_one_another(self):
        with self.assertRaisesRegex(RuntimeError, "contain one another"):
            installer.install_plugin(self.source, self.source / "nested/skills/webmind-claudecode")

    def test_existing_install_can_prepare_dependencies_in_place(self):
        self.install()
        with patch.object(installer, "prepare_environment") as prepare:
            result = installer.install_plugin(self.target, self.target, prepare)
        prepare.assert_called_once_with(self.target)
        self.assertFalse(result["copied"])
        self.assertIsNone(result["backup"])

    def test_dependency_failure_leaves_previous_install_and_cleans_stage(self):
        self.install()
        old = (self.target / "README.md").read_bytes()
        (self.source / "README.md").write_text("new", encoding="utf-8")
        def fail(stage):
            self.assertFalse(stage.is_relative_to(self.target.parent))
            raise RuntimeError("dependency failure")
        with self.assertRaisesRegex(RuntimeError, "dependency failure"):
            self.install(fail)
        self.assertEqual((self.target / "README.md").read_bytes(), old)
        self.assertEqual(list(self.config.glob(".webmind-stage-*")), [])
        self.assertFalse((self.config / "webmind-install-backups").exists())

    def test_replacement_failure_restores_previous_install(self):
        self.install()
        old = (self.target / "README.md").read_bytes()
        original = Path.rename
        def fail_stage(path, destination):
            if path.name.startswith(".webmind-stage-"):
                raise OSError("replacement failure")
            return original(path, destination)
        with patch.object(Path, "rename", fail_stage), self.assertRaisesRegex(OSError, "replacement failure"):
            self.install()
        self.assertEqual((self.target / "README.md").read_bytes(), old)
        self.assertEqual(list(self.config.glob(".webmind-stage-*")), [])

    def test_symlink_or_junction_destination_is_refused(self):
        actual = installer.is_link
        with patch.object(installer, "is_link", side_effect=lambda path: path == self.target or actual(path)):
            with self.assertRaisesRegex(RuntimeError, "symlink or junction"):
                self.install()
        self.assertFalse(self.config.exists())

    def test_reparse_point_in_mem_pointer_is_refused(self):
        self.install()
        pointer = self.target / installer.MEM_POINTER
        pointer.write_text("keep", encoding="utf-8")
        actual = installer.is_link
        with patch.object(installer, "is_link", side_effect=lambda path: path == pointer or actual(path)):
            with self.assertRaisesRegex(RuntimeError, "symlink or junction"):
                self.install()
        self.assertEqual(pointer.read_text(encoding="utf-8"), "keep")

    def run_main(self, arguments):
        output = io.StringIO()
        with patch.object(installer, "ROOT", self.source), contextlib.redirect_stdout(output):
            code = installer.main(arguments)
        self.assertEqual(code, 0)
        return json.loads(output.getvalue())

    def test_dry_run_creates_no_directories_or_subprocesses(self):
        with patch.object(installer.subprocess, "run") as run:
            report = self.run_main(["--dry-run"])
        run.assert_not_called()
        self.assertTrue(report["dry_run"])
        self.assertFalse(self.config.exists())
        self.assertFalse((self.root / "runtime").exists())

    def test_copy_only_does_not_install_dependencies_or_claim_host_loading(self):
        with patch.object(installer.subprocess, "run") as run:
            report = self.run_main(["--skip-deps"])
        run.assert_not_called()
        self.assertTrue(self.target.is_dir())
        self.assertFalse(report["dependencies_verified"])
        self.assertFalse(report["host_loading_verified"])

    def test_deps_only_does_not_create_a_second_installation(self):
        with patch.object(installer.platform, "system", return_value=installer.NATIVE_PLATFORM), \
             patch.object(installer, "prepare_environment") as prepare, \
             patch.object(installer, "check_host", return_value={"checked": False}):
            report = self.run_main(["--deps-only"])
        prepare.assert_called_once_with(self.source)
        self.assertFalse(self.config.exists())
        self.assertFalse(report["copied"])

    def test_wrong_native_platform_fails_before_copy_or_pip(self):
        with patch.object(installer.platform, "system", return_value="unsupported"), \
             patch.object(installer, "ROOT", self.source), \
             patch.object(installer.subprocess, "run") as run, contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(installer.main([]), 1)
        run.assert_not_called()
        self.assertFalse(self.config.exists())

    def test_enabled_other_origins_are_reported_without_unrelated_plugins(self):
        records = [{"id": "webmind-claudecode@old-desktop", "scope": "user", "enabled": True},
                   {"id": "webmind-claudecode@inline", "enabled": True},
                   {"id": "webmind-claudecode@disabled", "enabled": False},
                   {"id": "webmind-claudecode@skills-dir", "enabled": True},
                   {"id": "another-plugin@market", "enabled": True}]
        self.assertEqual([r["id"] for r in installer.conflicting_plugins(records)],
                         ["webmind-claudecode@old-desktop", "webmind-claudecode@inline"])

    def test_runtime_inside_plugin_is_refused_before_running_commands(self):
        with patch.dict(os.environ, {"WEBMIND_DATA_DIR": str(self.source / "runtime")}), \
             patch.object(installer.platform, "system", return_value=installer.NATIVE_PLATFORM), \
             patch.object(installer.subprocess, "run") as run:
            with self.assertRaisesRegex(RuntimeError, "outside the plugin"):
                installer.prepare_environment(self.source)
        run.assert_not_called()

    def test_dependencies_are_prepared_from_stage_before_replacement(self):
        commands = []
        def record(command, **kwargs):
            self.assertFalse(self.target.exists())
            commands.append(command)
        with patch.object(installer.platform, "system", return_value=installer.NATIVE_PLATFORM), \
             patch.object(installer, "ROOT", self.source), \
             patch.object(installer.subprocess, "run", side_effect=record):
            self.install(installer.prepare_environment)
        self.assertEqual(len(commands), 4)
        requirement = Path(commands[2][-1])
        self.assertTrue(requirement.parent.name.startswith(".webmind-stage-"))
        self.assertEqual(requirement.name, "requirements.txt")
        self.assertEqual(Path(commands[3][2]).parent.parent, requirement.parent)
        self.assertTrue(self.target.is_dir())

    def test_invalid_manifest_type_is_a_controlled_failure(self):
        (self.source / ".claude-plugin/plugin.json").write_text("[]", encoding="utf-8")
        with self.assertRaisesRegex(RuntimeError, "complete WebMind"):
            self.install()
        self.assertFalse(self.config.exists())

    def test_installed_doctor_runs_after_download_is_moved(self):
        self.install()
        self.source.rename(self.source.with_name("download removed from its original location"))
        environment = os.environ.copy()
        environment["PYTHONIOENCODING"] = "utf-8"
        environment.pop("WEBMIND_MEM_LOCATION_FILE", None)
        result = subprocess.run([sys.executable, "-B", str(self.target / "scripts/webmind.py"), "doctor", "--json"],
                                cwd=self.root, env=environment, capture_output=True, text=True, encoding="utf-8")
        self.assertIn(result.returncode, (0, 1))  # A non-native test runner can still inspect placement.
        report = json.loads(result.stdout)
        self.assertEqual(Path(report["plugin_root"]), self.target)
        self.assertTrue(all(report["skills"].values()))
        self.assertEqual(len(report["skills"]), 6)
        self.assertTrue(report["installation"]["in_personal_skills_directory"])
        self.assertFalse(report["installation"]["host_loading_verified"])


if __name__ == "__main__":
    unittest.main()
