#!/usr/bin/env python3
"""Stable dispatcher for the webmind-claudecode plugin."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import platform
import subprocess
import sys
from pathlib import Path


MINIMUM_PYTHON = (3, 10)
PLUGIN_ROOT = Path(__file__).resolve().parents[1]
MEM_LOCATION_FILE = PLUGIN_ROOT / "skills" / "webmind-mem" / "mem-location.json"
INIT_MEM_COMMANDS = {"init-status", "scan", "name-info", "self-check", "init"}

COMPONENTS = {
    "cdp": PLUGIN_ROOT / "skills" / "webmind-cdp" / "scripts" / "webmind_cdp.py",
    "screenshot": PLUGIN_ROOT / "skills" / "webmind-screenshot" / "scripts" / "webmind_screenshot.py",
    "mouse": PLUGIN_ROOT / "skills" / "webmind-mouse-control" / "scripts" / "webmind_mouse_control.py",
    "typing": PLUGIN_ROOT / "skills" / "webmind-typing" / "scripts" / "webmind_typing.py",
    "mem": PLUGIN_ROOT / "skills" / "webmind-mem" / "scripts" / "webmind_mem.py",
}



def mem_module():
    spec = importlib.util.spec_from_file_location("_webmind_mem_runtime", COMPONENTS["mem"])
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def initialization_status():
    return mem_module().initialization_status()


def is_initialization_command(component, arguments):
    return component == "mem" and any(item in INIT_MEM_COMMANDS for item in arguments)

def ensure_supported_runtime() -> None:
    if sys.version_info < MINIMUM_PYTHON:
        raise RuntimeError('webmind-claudecode requires Python 3.10 or newer')
    if platform.system() != 'Darwin':
        raise RuntimeError('This edition requires a native macOS desktop and native Python.')


def doctor() -> int:
    dependencies = {
        "Pillow": importlib.util.find_spec("PIL") is not None,
        "mss": importlib.util.find_spec("mss") is not None,
        "PyAutoGUI": importlib.util.find_spec("pyautogui") is not None,
    }
    dependencies["Quartz"] = importlib.util.find_spec("Quartz") is not None
    scripts = {name: path.is_file() for name, path in COMPONENTS.items()}
    ok = (
        sys.version_info >= MINIMUM_PYTHON
        and platform.system() == 'Darwin'
        and all(dependencies.values())
        and all(scripts.values())
    )
    ok = ok and platform.system() == 'Darwin'
    init = initialization_status()
    print(
        json.dumps(
            {
                "ok": ok,
                "python": platform.python_version(),
                "platform": platform.platform(),
                "plugin_root": str(PLUGIN_ROOT),
                "dependencies": dependencies,
                "components": scripts,
                "initialization": init,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0 if ok else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run one webmind-claudecode plugin component.")
    parser.add_argument("component", choices=[*COMPONENTS, "doctor"])
    parser.add_argument("arguments", nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)
    if args.component == "doctor":
        return doctor()
    try:
        ensure_supported_runtime()
        help_only = "--help" in args.arguments or "-h" in args.arguments
        if not help_only and not is_initialization_command(args.component, args.arguments):
            init = initialization_status()
            if not init.get("initialized"):
                raise RuntimeError(
                    "webmind initialization is required before normal use. Recommend the usage tutorial and safety notice, "
                    "obtain the user choice to continue, then use mem scan/name-info/init to select an external xxx-yyy-mem folder."
                )
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    script = COMPONENTS[args.component]
    env = os.environ.copy()
    env["WEBMIND_MEM_LOCATION_FILE"] = str(MEM_LOCATION_FILE)
    completed = subprocess.run([sys.executable, str(script), *args.arguments], check=False, env=env)
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
