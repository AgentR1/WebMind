#!/usr/bin/env python3
"""Stable dispatcher for the WebUse Claude Code plugin."""

from __future__ import annotations

import argparse
import importlib.util
import json
import platform
import subprocess
import sys
from pathlib import Path


MINIMUM_PYTHON = (3, 10)
PLUGIN_ROOT = Path(__file__).resolve().parents[1]
COMPONENTS = {
    "cdp": PLUGIN_ROOT / "skills" / "webuse-cdp" / "scripts" / "webuse_cdp.py",
    "screenshot": PLUGIN_ROOT / "skills" / "webuse-screenshot" / "scripts" / "webuse_screenshot.py",
    "mouse": PLUGIN_ROOT / "skills" / "webuse-mouse-control" / "scripts" / "webuse_mouse_control.py",
    "typing": PLUGIN_ROOT / "skills" / "webuse-typing" / "scripts" / "webuse_typing.py",
    "mem": PLUGIN_ROOT / "skills" / "webuse-mem" / "scripts" / "webuse_mem.py",
}


def ensure_supported_runtime() -> None:
    if sys.version_info < MINIMUM_PYTHON:
        required = ".".join(map(str, MINIMUM_PYTHON))
        actual = platform.python_version()
        raise RuntimeError(f"WebUse requires Python {required} or newer; found {actual}")
    if platform.system() not in {"Windows", "Darwin"}:
        raise RuntimeError("this plugin build supports Windows and macOS")


def doctor() -> int:
    dependencies = {
        "Pillow": importlib.util.find_spec("PIL") is not None,
        "mss": importlib.util.find_spec("mss") is not None,
        "PyAutoGUI": importlib.util.find_spec("pyautogui") is not None,
    }
    scripts = {name: path.is_file() for name, path in COMPONENTS.items()}
    ok = (
        sys.version_info >= MINIMUM_PYTHON
        and platform.system() in {"Windows", "Darwin"}
        and all(dependencies.values())
        and all(scripts.values())
    )
    print(
        json.dumps(
            {
                "ok": ok,
                "python": platform.python_version(),
                "platform": platform.platform(),
                "plugin_root": str(PLUGIN_ROOT),
                "dependencies": dependencies,
                "components": scripts,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0 if ok else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run one WebUse plugin component.")
    parser.add_argument("component", choices=[*COMPONENTS, "doctor"])
    parser.add_argument("arguments", nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)
    if args.component == "doctor":
        return doctor()
    try:
        ensure_supported_runtime()
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    script = COMPONENTS[args.component]
    completed = subprocess.run([sys.executable, str(script), *args.arguments], check=False)
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
