#!/usr/bin/env python3
"""Keyboard automation helper for WebMind agents.

This script intentionally supports only standard keyboard text for literal typing.
Chinese or other IME-driven text should not be sent through this tool.
"""

from __future__ import annotations

import argparse
import importlib
import json
import math
import string
import sys
import time
from dataclasses import asdict, dataclass
from typing import Any, Iterable

# Import only for commands that need GUI access. --help works without a display.
pyautogui = None
IMPORT_ERROR = None

PRINTABLE_ASCII = set(string.printable)  # includes tab/newline/carriage return
DISALLOWED_CONTROL_CHARS = {"\x0b", "\x0c"}

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
    if result.action in {"type", "press", "hotkey", "down", "up"}:
        payload["outcome_verified"] = False
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
    global pyautogui, IMPORT_ERROR
    if pyautogui is None:
        try:
            pyautogui = importlib.import_module("pyautogui")
        except Exception as exc:
            IMPORT_ERROR = exc
            raise RuntimeError(
                f"pyautogui is not available: {exc}. "
                "Install with: python -m pip install -r requirements-desktop.txt"
            ) from exc
    pyautogui.FAILSAFE = True


def english_warning() -> str:
    return (
        "Before this keyboard action, WebMind agents must ensure the active input "
        "method / keyboard layout is English. This script cannot verify IME state."
    )


def normalize_key(key: str) -> str:
    if key == " ":
        return "space"
    normalized = key.strip().lower()
    normalized = KEY_ALIASES.get(normalized, normalized)
    return normalized


def supported_keys() -> set[str]:
    require_pyautogui()
    keys = set(getattr(pyautogui, "KEYBOARD_KEYS", []))
    return keys


def validate_key(key: str) -> str:
    normalized = normalize_key(key)
    keys = supported_keys()
    if normalized not in keys:
        raise ValueError(
            f"Unsupported key '{key}'. Run `python scripts/webmind_typing.py list-keys` "
            "to see supported key names."
        )
    return normalized


def validate_text(text: str) -> None:
    invalid = []
    for ch in text:
        if ch not in PRINTABLE_ASCII or ch in DISALLOWED_CONTROL_CHARS:
            invalid.append(ch)
    if invalid:
        shown = "".join(sorted(set(invalid)))
        raise ValueError(
            "Text contains characters outside standard English keyboard input: "
            f"{shown!r}. Do not type Chinese or IME-driven text through this skill."
        )


def sleep_before(seconds: float) -> None:
    if seconds > 0:
        time.sleep(seconds)


def action_type(args: argparse.Namespace) -> Result:
    validate_text(args.text)
    require_pyautogui()
    sleep_before(args.delay)
    pyautogui.write(args.text, interval=args.interval)
    return Result(
        ok=True,
        action="type",
        message="typed standard keyboard text",
        details={"length": len(args.text), "interval": args.interval, "delay": args.delay},
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


def release_keys(keys: Iterable[str]) -> None:
    """Release inputs even at a failsafe corner, then restore the normal guard."""
    failsafe = pyautogui.FAILSAFE
    release_error = None
    try:
        pyautogui.FAILSAFE = False
        for key in reversed(list(keys)):
            try:
                pyautogui.keyUp(key)
            except BaseException as exc:
                if release_error is None:
                    release_error = exc
    finally:
        pyautogui.FAILSAFE = failsafe
    if release_error is not None:
        raise release_error


def action_hotkey(args: argparse.Namespace) -> Result:
    require_pyautogui()
    keys = [validate_key(key) for key in args.keys]
    sleep_before(args.delay)
    attempted = []
    try:
        for key in keys:
            attempted.append(key)
            pyautogui.keyDown(key)
            if args.interval:
                time.sleep(args.interval)
    finally:
        # Releasing must still work after an input error or a failsafe interrupt.
        release_keys(attempted)
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
    release_keys([key])
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
        "Before typing, WebMind agents must ensure the active input method is English.",
    ]
    try:
        require_pyautogui()
    except RuntimeError:
        pass
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
    parser.add_argument("--delay", type=float, default=0.0, help="seconds to wait before performing the action")
    parser.add_argument("--json", action="store_true", help="print machine-readable JSON output")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="webmind_typing.py",
        description="WebMind: simulate English keyboard typing, key presses, holds, releases, and hotkeys.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    p_type = subparsers.add_parser("type", help="type literal standard English keyboard text")
    p_type.add_argument("--text", required=True, help="text to type; must be standard keyboard / printable ASCII")
    p_type.add_argument("--interval", type=float, default=0.01, help="seconds between characters")
    add_common_action_args(p_type)
    p_type.set_defaults(func=action_type)

    p_press = subparsers.add_parser("press", help="press one key one or more times")
    p_press.add_argument("--key", required=True, help="key name, for example enter, tab, space, a, f5")
    p_press.add_argument("--presses", type=int, default=1, help="number of repeated presses")
    p_press.add_argument("--interval", type=float, default=0.0, help="seconds between repeated presses")
    add_common_action_args(p_press)
    p_press.set_defaults(func=action_press)

    p_hotkey = subparsers.add_parser("hotkey", aliases=["shortcut"], help="press a keyboard shortcut")
    p_hotkey.add_argument("--keys", nargs="+", required=True, help="ordered keys, for example: ctrl shift p")
    p_hotkey.add_argument("--interval", type=float, default=0.0, help="seconds between key down/up operations")
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
    parser = build_parser()
    args = parser.parse_args(argv)
    as_json = bool(getattr(args, "json", False))
    try:
        for name in ("delay", "interval"):
            if hasattr(args, name):
                value = float(getattr(args, name))
                if not math.isfinite(value) or value < 0:
                    raise ValueError(f"--{name} must be a finite, nonnegative number")
        if hasattr(args, "presses") and args.presses <= 0:
            raise ValueError("--presses must be a positive integer")
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
