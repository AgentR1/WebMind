#!/usr/bin/env python3
"""Keyboard automation helper for Claude Code.

This script intentionally supports only standard keyboard text for literal typing.
Chinese or other IME-driven text should not be sent through this tool.
"""

from __future__ import annotations

import argparse
import json
import math
import platform
import sys
import time
from dataclasses import asdict, dataclass
from typing import Any, Iterable


def configure_utf8_stdio() -> None:
    """Make CLI text I/O independent of the host console code page."""
    for name in ("stdin", "stdout", "stderr"):
        stream = getattr(sys, name)
        reconfigure = getattr(stream, "reconfigure", None)
        if not callable(reconfigure):
            continue
        try:
            reconfigure(encoding="utf-8", errors="strict")
        except (OSError, ValueError):
            pass


try:
    import pyautogui
except Exception as exc:  # pragma: no cover - depends on runtime environment
    pyautogui = None  # type: ignore[assignment]
    IMPORT_ERROR = exc
else:
    IMPORT_ERROR = None

MAX_STDIN_TEXT_CHARS = 1_000_000

KEY_ALIASES = {
    "cmd": "command",
    "command": "command",
    "option": "alt",
    "return": "enter",
    "esc": "escape",
    "spacebar": "space",
    "control": "ctrl",
    "windows": "win",
    "super": "win",
}


@dataclass
class Result:
    ok: bool
    action: str
    message: str
    details: dict[str, Any]
    warnings: list[str]


def emit(result: Result, as_json: bool) -> int:
    payload = asdict(result)
    if as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        status = "OK" if result.ok else "ERROR"
        print(f"[{status}] {result.message}")
        if result.details:
            for key, value in result.details.items():
                print(f"{key}: {value}")
        if result.warnings:
            print("warnings:")
            for warning in result.warnings:
                print(f"- {warning}")
    return 0 if result.ok else 1


def require_pyautogui() -> None:
    if pyautogui is None:
        raise RuntimeError(f"pyautogui is not available: {IMPORT_ERROR}")
    pyautogui.FAILSAFE = True


def english_warning() -> str:
    return (
        "Before this keyboard action, Claude Code must ensure the active input "
        "method / keyboard layout is English. This script cannot verify IME state."
    )


def normalize_key(key: str) -> str:
    normalized = key.strip().lower()
    if normalized in {"primary", "mod"}:
        return "command" if platform.system() == "Darwin" else "ctrl"
    normalized = KEY_ALIASES.get(normalized, normalized)
    if normalized == " ":
        normalized = "space"
    return normalized


def supported_keys() -> set[str]:
    require_pyautogui()
    keys = set(getattr(pyautogui, "KEYBOARD_KEYS", []))
    keys.update(KEY_ALIASES.values())
    return keys


def validate_key(key: str) -> str:
    normalized = normalize_key(key)
    keys = supported_keys()
    if normalized not in keys:
        raise ValueError(
            f"Unsupported key '{key}'. Run the WebUse `typing list-keys` command "
            "to see supported key names."
        )
    return normalized


def validate_text(text: str) -> None:
    invalid = [ch for ch in text if not 32 <= ord(ch) <= 126]
    if invalid:
        shown = "".join(sorted(set(invalid)))
        raise ValueError(
            "Text contains control characters or characters outside printable ASCII: "
            f"{shown!r}. Use `press` for Tab/Enter and do not type IME-driven text through this skill."
        )


def nonnegative_float(value: str) -> float:
    parsed = float(value)
    if not math.isfinite(parsed) or parsed < 0:
        raise argparse.ArgumentTypeError("value must be a finite number greater than or equal to zero")
    return parsed


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("value must be a positive integer")
    return parsed


def sleep_before(seconds: float) -> None:
    if seconds > 0:
        time.sleep(seconds)


def action_type(args: argparse.Namespace) -> Result:
    text = args.text
    if args.stdin:
        if sys.stdin.isatty():
            raise ValueError("--stdin requires text piped on standard input")
        text = sys.stdin.read(MAX_STDIN_TEXT_CHARS + 1)
        if len(text) > MAX_STDIN_TEXT_CHARS:
            raise ValueError("standard input exceeds the 1,000,000 character safety limit")
        # Shell pipelines commonly add one record terminator. Remove that one
        # terminator; embedded control characters remain invalid below.
        if text.endswith("\r\n"):
            text = text[:-2]
        elif text.endswith("\n"):
            text = text[:-1]
    validate_text(text)
    require_pyautogui()
    sleep_before(args.delay)
    pyautogui.write(text, interval=args.interval)
    return Result(
        ok=True,
        action="type",
        message="typed standard keyboard text",
        details={"length": len(text), "interval": args.interval, "delay": args.delay},
        warnings=[english_warning()],
    )


def action_press(args: argparse.Namespace) -> Result:
    require_pyautogui()
    key = validate_key(args.key)
    sleep_before(args.delay)
    pyautogui.press(key, presses=args.presses, interval=args.interval)
    return Result(
        ok=True,
        action="press",
        message=f"pressed key: {key}",
        details={"key": key, "presses": args.presses, "interval": args.interval, "delay": args.delay},
        warnings=[english_warning()],
    )


def action_hotkey(args: argparse.Namespace) -> Result:
    require_pyautogui()
    keys = [validate_key(key) for key in args.keys]
    sleep_before(args.delay)
    pyautogui.hotkey(*keys, interval=args.interval)
    return Result(
        ok=True,
        action="hotkey",
        message="ran hotkey: " + "+".join(keys),
        details={"keys": keys, "interval": args.interval, "delay": args.delay},
        warnings=[english_warning()],
    )


def action_down(args: argparse.Namespace) -> Result:
    require_pyautogui()
    key = validate_key(args.key)
    sleep_before(args.delay)
    pyautogui.keyDown(key)
    return Result(
        ok=True,
        action="down",
        message=f"held key down: {key}",
        details={"key": key, "delay": args.delay},
        warnings=[english_warning(), "Always release held keys with the matching `up` command."],
    )


def action_up(args: argparse.Namespace) -> Result:
    require_pyautogui()
    key = validate_key(args.key)
    sleep_before(args.delay)
    pyautogui.keyUp(key)
    return Result(
        ok=True,
        action="up",
        message=f"released key: {key}",
        details={"key": key, "delay": args.delay},
        warnings=[english_warning()],
    )


def action_list_keys(args: argparse.Namespace) -> Result:
    keys = sorted(supported_keys())
    if args.json:
        return Result(True, "list-keys", "listed supported keys", {"keys": keys}, [])
    for key in keys:
        print(key)
    return Result(True, "list-keys", "listed supported keys", {"count": len(keys)}, [])


def action_self_check(args: argparse.Namespace) -> Result:
    warnings = [
        "This check cannot verify GUI permissions, focused input target, or current input method.",
        "Before typing, Claude Code must ensure the active input method is English.",
    ]
    details: dict[str, Any] = {
        "python": sys.version.split()[0],
        "pyautogui_available": pyautogui is not None,
    }
    if pyautogui is None:
        details["import_error"] = str(IMPORT_ERROR)
        return Result(False, "self-check", "pyautogui is not available", details, warnings)
    try:
        details["screen_size"] = tuple(pyautogui.size())
        details["failsafe"] = bool(pyautogui.FAILSAFE)
        details["supported_key_count"] = len(getattr(pyautogui, "KEYBOARD_KEYS", []))
    except Exception as exc:
        details["runtime_error"] = str(exc)
        return Result(False, "self-check", "pyautogui loaded but GUI access failed", details, warnings)
    return Result(True, "self-check", "runtime dependency is available", details, warnings)


def add_common_action_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--delay", type=nonnegative_float, default=0.0, help="seconds to wait before performing the action")
    parser.add_argument("--json", action="store_true", help="print machine-readable JSON output")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="webuse typing",
        description="Simulate English keyboard typing, key presses, holds, releases, and hotkeys.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    p_type = subparsers.add_parser("type", help="type literal standard English keyboard text")
    type_source = p_type.add_mutually_exclusive_group(required=True)
    type_source.add_argument("--text", help="text to type; must be printable ASCII and non-sensitive")
    type_source.add_argument("--stdin", action="store_true", help="read printable ASCII from stdin to avoid exposing it in process arguments")
    p_type.add_argument("--interval", type=nonnegative_float, default=0.01, help="seconds between characters")
    add_common_action_args(p_type)
    p_type.set_defaults(func=action_type)

    p_press = subparsers.add_parser("press", help="press one key one or more times")
    p_press.add_argument("--key", required=True, help="key name, for example enter, tab, space, a, f5")
    p_press.add_argument("--presses", type=positive_int, default=1, help="number of repeated presses")
    p_press.add_argument("--interval", type=nonnegative_float, default=0.0, help="seconds between repeated presses")
    add_common_action_args(p_press)
    p_press.set_defaults(func=action_press)

    p_hotkey = subparsers.add_parser("hotkey", aliases=["shortcut"], help="press a keyboard shortcut")
    p_hotkey.add_argument("--keys", nargs="+", required=True, help="ordered keys, for example: ctrl shift p")
    p_hotkey.add_argument("--interval", type=nonnegative_float, default=0.0, help="seconds between key down/up operations")
    add_common_action_args(p_hotkey)
    p_hotkey.set_defaults(func=action_hotkey)

    p_down = subparsers.add_parser("down", help="hold one key down")
    p_down.add_argument("--key", required=True, help="key name to hold")
    add_common_action_args(p_down)
    p_down.set_defaults(func=action_down)

    p_up = subparsers.add_parser("up", help="release one held key")
    p_up.add_argument("--key", required=True, help="key name to release")
    add_common_action_args(p_up)
    p_up.set_defaults(func=action_up)

    p_list = subparsers.add_parser("list-keys", help="print supported pyautogui key names")
    p_list.add_argument("--json", action="store_true", help="print machine-readable JSON output")
    p_list.set_defaults(func=action_list_keys)

    p_check = subparsers.add_parser("self-check", help="check runtime dependency and basic GUI access")
    p_check.add_argument("--json", action="store_true", help="print machine-readable JSON output")
    p_check.set_defaults(func=action_self_check)

    return parser


def main(argv: list[str] | None = None) -> int:
    configure_utf8_stdio()
    parser = build_parser()
    args = parser.parse_args(argv)
    as_json = bool(getattr(args, "json", False))
    try:
        result = args.func(args)
    except Exception as exc:
        result = Result(
            ok=False,
            action=getattr(args, "command", "unknown"),
            message=str(exc),
            details={},
            warnings=[english_warning()],
        )
    return emit(result, as_json)


if __name__ == "__main__":
    raise SystemExit(main())
