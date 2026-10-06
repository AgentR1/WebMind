#!/usr/bin/env python3
"""Copy the complete plugin into Claude's personal skills directory."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import platform
import shutil
import stat
import subprocess
import sys
import time
import uuid


NATIVE_PLATFORM = "Darwin"
PLUGIN_NAME = "webmind-claudecode"
ROOT = Path(__file__).resolve().parents[1]
MARKER = ".webmind-install.json"
MANAGER = "webmind-skills-directory-installer"
MEM_POINTER = Path("skills/webmind-mem/mem-location.json")
SKILLS = ("webmind-cdp", "webmind-screenshot", "webmind-mouse-control",
          "webmind-typing", "webmind-mem", "webmind-wait")
COMPONENT_SCRIPTS = ("webmind-cdp/scripts/webmind_cdp.py",
                     "webmind-screenshot/scripts/webmind_screenshot.py",
                     "webmind-mouse-control/scripts/webmind_mouse_control.py",
                     "webmind-typing/scripts/webmind_typing.py",
                     "webmind-mem/scripts/webmind_mem.py")


def config_root() -> Path:
    return Path(os.environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude").expanduser().absolute()


def default_target() -> Path:
    return config_root() / "skills" / PLUGIN_NAME


def data_root() -> Path:
    if os.environ.get("WEBMIND_DATA_DIR"):
        return Path(os.environ["WEBMIND_DATA_DIR"]).expanduser().absolute()
    if NATIVE_PLATFORM == "Windows":
        return Path(os.environ.get("LOCALAPPDATA") or Path.home() / "AppData/Local") / "WebMind"
    return Path.home() / "Library/Application Support/WebMind"


def is_link(path: Path) -> bool:
    try:
        info = path.lstat()
    except FileNotFoundError:
        return False
    return stat.S_ISLNK(info.st_mode) or bool(
        getattr(info, "st_file_attributes", 0) & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400))


def plain_path(path: Path) -> Path:
    path = path.expanduser().absolute()
    for item in (path, *path.parents):
        if is_link(item):
            raise RuntimeError(f"Refusing a symlink or junction: {item}")
    return path.resolve()


def validate_package(root: Path) -> dict:
    launcher = "webmind.ps1" if NATIVE_PLATFORM == "Windows" else "webmind.sh"
    required = [".claude-plugin/plugin.json", ".claude-plugin/marketplace.json",
                "requirements.txt", "使用教程.md", "安全须知.md",
                "scripts/install.py", "scripts/webmind.py", "scripts/runtime.py", f"scripts/{launcher}"]
    required += [f"skills/{name}/SKILL.md" for name in SKILLS]
    required += [f"skills/{name}" for name in COMPONENT_SCRIPTS]
    for name in required:
        path = plain_path(root / name)
        if not path.is_file() or not path.is_relative_to(root):
            raise RuntimeError(f"Incomplete plugin: {name}")
    manifest = json.loads((root / ".claude-plugin/plugin.json").read_text(encoding="utf-8"))
    if not isinstance(manifest, dict) or manifest.get("name") != PLUGIN_NAME:
        raise RuntimeError("The source is not the complete WebMind Claude Code plugin.")
    return manifest


def installation_status(root: Path) -> dict:
    expected = default_target().resolve()
    return {"expected_plugin_root": str(expected),
            "in_personal_skills_directory": root.resolve() == expected,
            "host_loading_verified": False}


def read_owner(target: Path) -> dict:
    marker = plain_path(target / MARKER)
    try:
        owner = json.loads(marker.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise RuntimeError(f"Refusing to overwrite an unrecognized directory: {target}") from exc
    if not isinstance(owner, dict) or any(owner.get(key) != value for key, value in {
        "schema": 1, "manager": MANAGER, "plugin": PLUGIN_NAME, "platform": NATIVE_PLATFORM,
    }.items()):
        raise RuntimeError(f"Refusing an unknown or different-platform installation: {target}")
    return owner


def validate_destination(source: Path, target: Path) -> None:
    if source != target and (source.is_relative_to(target) or target.is_relative_to(source)):
        raise RuntimeError("The source and destination must not contain one another.")
    if target.exists():
        if not target.is_dir():
            raise RuntimeError(f"Destination is not a directory: {target}")
        read_owner(target)


def ignore_runtime(directory: str, names: list[str]) -> set[str]:
    ignored = set()
    for name in names:
        lower = name.lower()
        if (lower in {".git", ".venv", "__pycache__", ".pytest_cache", ".claude", ".agents", ".codex",
                      MARKER, "mem-location.json", "webmind-profile.json", "devtoolsactiveport",
                      "cookies", "login data", "screenshots", "logs"}
                or (lower.endswith("-mem") and lower != "webmind-mem")
                or lower.endswith(("-profile", ".pyc", ".pyo", ".png", ".jpg", ".jpeg",
                                   ".log", ".key", ".pem", ".p12", ".pfx"))
                or lower.startswith((".env", ".tmp-", ".webmind-stage-"))):
            ignored.add(name)
        elif is_link(Path(directory) / name):
            raise RuntimeError(f"Refusing to copy a symlink or junction: {Path(directory) / name}")
    return ignored


def retry_readonly_cleanup(function, path, error) -> None:
    if os.name != "nt" or not isinstance(error[1], PermissionError):
        raise error[1]
    os.chmod(path, 0o777)
    for attempt in range(5):
        try:
            function(path)
            return
        except OSError as exc:
            if getattr(exc, "winerror", None) not in (5, 32, 33) or attempt == 4:
                raise
            time.sleep(0.1)


def remove_stage(stage: Path, parent: Path) -> None:
    # Check the absolute boundary before recursively deleting a computed path.
    checked = plain_path(stage)
    if checked.parent != plain_path(parent) or not checked.name.startswith(".webmind-stage-"):
        raise RuntimeError("Invalid staging cleanup path.")
    if checked.exists():
        shutil.rmtree(checked, onerror=retry_readonly_cleanup)


def rename_owned(source: Path, target: Path) -> None:
    for attempt in range(5):
        plain_path(source)
        plain_path(target)
        try:
            source.rename(target)
            return
        except OSError as exc:
            if os.name != "nt" or getattr(exc, "winerror", None) not in (5, 32, 33) or attempt == 4:
                raise
            # Antivirus/cloud scanners can briefly hold a directory after copying.
            time.sleep(0.1)


def install_plugin(source: Path, target: Path, prepare=None) -> dict:
    source, target = plain_path(source), plain_path(target)
    manifest = validate_package(source)
    validate_destination(source, target)
    if source == target:
        if prepare:
            prepare(target)
        return {"plugin_root": str(target), "copied": False, "backup": None}
    target.parent.mkdir(parents=True, exist_ok=True)
    # Staging and backup plugins stay outside skills/ so Claude cannot discover them.
    stage_parent = target.parent.parent
    stage = stage_parent / (".webmind-stage-" + uuid.uuid4().hex)
    # Inherit the config directory ACL on Windows; mode 0700 changes it on Python 3.13.
    stage.mkdir(mode=0o777 if os.name == "nt" else 0o700)
    backup = None
    try:
        shutil.copytree(source, stage, dirs_exist_ok=True, ignore=ignore_runtime)
        if os.name == "nt":
            stage.chmod(0o777)
        validate_package(stage)
        if target.exists():
            pointer = plain_path(target / MEM_POINTER)
            if pointer.is_file():
                shutil.copy2(pointer, stage / MEM_POINTER)
        owner = {"schema": 1, "manager": MANAGER, "plugin": PLUGIN_NAME,
                 "platform": NATIVE_PLATFORM, "version": manifest.get("version"),
                 "installed_at": datetime.now(timezone.utc).isoformat()}
        (stage / MARKER).write_text(json.dumps(owner, indent=2) + "\n", encoding="utf-8")
        if prepare:
            prepare(stage)
        plain_path(target)
        validate_destination(source, target)
        if target.exists():
            backup_parent = plain_path(stage_parent / "webmind-install-backups")
            backup_parent.mkdir(parents=True, exist_ok=True)
            backup = backup_parent / (PLUGIN_NAME + "-" + uuid.uuid4().hex)
            rename_owned(target, backup)
        try:
            rename_owned(stage, target)
        except OSError:
            if backup is not None:
                rename_owned(backup, target)
            raise
    finally:
        remove_stage(stage, stage_parent)
    return {"plugin_root": str(target), "copied": True, "backup": str(backup) if backup else None}


def prepare_environment(root: Path) -> None:
    if platform.system() != NATIVE_PLATFORM:
        raise RuntimeError(f"Dependency installation requires native {NATIVE_PLATFORM} Python.")
    runtime = plain_path(data_root())
    if any(runtime.is_relative_to(path.resolve()) for path in (ROOT, root, default_target())):
        raise RuntimeError("WEBMIND_DATA_DIR must be outside the plugin directory.")
    venv = plain_path(runtime / ".venv")
    subprocess.run([sys.executable, "-m", "venv", str(venv)], check=True)
    python = venv / ("Scripts/python.exe" if NATIVE_PLATFORM == "Windows" else "bin/python")
    subprocess.run([str(python), "-m", "pip", "install", "--upgrade", "pip"], check=True)
    subprocess.run([str(python), "-m", "pip", "install", "-r", str(root / "requirements.txt")], check=True)
    subprocess.run([str(python), "-B", str(root / "scripts/webmind.py"), "doctor", "--json"], check=True)


def conflicting_plugins(records) -> list[dict]:
    if isinstance(records, dict):
        records = records.get("installed", records.get("plugins", []))
    if not isinstance(records, list):
        raise ValueError("Unrecognized plugin list output")
    conflicts = []
    for entry in records:
        if not isinstance(entry, dict):
            continue
        identifier = entry.get("id", entry.get("name", ""))
        if (isinstance(identifier, str) and identifier.startswith(PLUGIN_NAME + "@")
                and identifier != PLUGIN_NAME + "@skills-dir" and entry.get("enabled") is not False):
            conflicts.append({"id": identifier, "scope": entry.get("scope"), "enabled": entry.get("enabled")})
    return conflicts


def check_host() -> dict:
    executable = shutil.which("claude")
    if not executable:
        return {"checked": False, "reason": "Claude CLI unavailable; verify loading in the new conversation."}
    try:
        result = subprocess.run([executable, "plugin", "list", "--json"],
                                capture_output=True, text=True, encoding="utf-8", timeout=15, check=True)
        return {"checked": True, "possible_conflicts": conflicting_plugins(json.loads(result.stdout))}
    except (OSError, ValueError, subprocess.SubprocessError):
        return {"checked": False, "reason": "Plugin list unavailable; verify loading in the new conversation."}


def main(argv=None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--deps-only", action="store_true", help="Prepare dependencies for this existing plugin; do not copy it.")
    parser.add_argument("--skip-deps", action="store_true", help="Copy files only; dependency readiness remains unverified.")
    parser.add_argument("--dry-run", action="store_true", help="Validate and show the plan without creating files or running commands.")
    args = parser.parse_args(argv)
    try:
        if sys.version_info < (3, 10):
            raise RuntimeError("Python 3.10 or newer is required.")
        if args.deps_only and args.skip_deps:
            raise RuntimeError("--deps-only and --skip-deps cannot be combined.")
        source = plain_path(ROOT)
        validate_package(source)
        target = source if args.deps_only else plain_path(default_target())
        if not args.deps_only:
            validate_destination(source, target)
        if not args.dry_run and not args.skip_deps and platform.system() != NATIVE_PLATFORM:
            raise RuntimeError(f"This edition requires native {NATIVE_PLATFORM} Python.")
        if args.dry_run:
            report = {"dry_run": True, "source": str(source), "plugin_root": str(target),
                      "runtime_root": str(data_root()), "deps_only": args.deps_only,
                      "prepare_dependencies": not args.skip_deps, "host_loading_verified": False}
        else:
            if args.deps_only:
                prepare_environment(source)
                report = {"plugin_root": str(source), "copied": False, "backup": None}
            else:
                report = install_plugin(source, target, None if args.skip_deps else prepare_environment)
            report.update({"runtime_root": str(data_root()), "dependencies_verified": not args.skip_deps,
                           "host_loading_verified": False,
                           "next": "Restart Claude Code; in a NEW conversation verify the loaded six skills and actual plugin_root before Mem initialization."})
            if not args.skip_deps:
                report["host_plugins"] = check_host()
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
