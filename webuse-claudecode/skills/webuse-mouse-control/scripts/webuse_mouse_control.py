#!/usr/bin/env python3
"""Mouse control utility for Claude Code.

Provides deterministic commands for moving the pointer, sliding it by an offset,
left-clicking, left-button down/up/hold, right-clicking, and mouse wheel scrolling.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import time
from dataclasses import dataclass, asdict
from typing import Any, Dict, Optional, Tuple


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


@dataclass
class Point:
    x: int
    y: int


@dataclass
class Screen:
    left: int
    top: int
    width: int
    height: int

    @property
    def right(self) -> int:
        return self.left + self.width

    @property
    def bottom(self) -> int:
        return self.top + self.height


def load_pyautogui():
    try:
        import pyautogui  # type: ignore
    except Exception as exc:  # pragma: no cover - depends on runtime environment
        raise RuntimeError(
            "pyautogui is not installed or cannot access the GUI session. "
            "Run the WebUse plugin installer for this platform."
        ) from exc
    pyautogui.FAILSAFE = True
    return pyautogui


def get_screen_and_position(pyautogui) -> Tuple[Screen, Point]:
    try:
        import mss  # type: ignore

        with mss.mss() as capture:
            monitor = capture.monitors[0]
        screen = Screen(
            left=int(monitor.get("left", 0)),
            top=int(monitor.get("top", 0)),
            width=int(monitor["width"]),
            height=int(monitor["height"]),
        )
    except Exception:
        width, height = pyautogui.size()
        screen = Screen(left=0, top=0, width=int(width), height=int(height))
    x, y = pyautogui.position()
    return screen, Point(int(x), int(y))


def validate_coordinate(screen: Screen, x: int, y: int) -> None:
    if x < screen.left or y < screen.top or x >= screen.right or y >= screen.bottom:
        raise ValueError(
            f"coordinate out of bounds: x={x}, y={y}; "
            f"virtual desktop is left={screen.left}, top={screen.top}, "
            f"width={screen.width}, height={screen.height}; "
            f"valid x={screen.left}..{screen.right - 1}, y={screen.top}..{screen.bottom - 1}"
        )


def maybe_move_to(pyautogui, screen: Screen, x: Optional[int], y: Optional[int], duration: float) -> None:
    if x is None and y is None:
        return
    if x is None or y is None:
        raise ValueError("both --x and --y are required when moving before an action")
    validate_coordinate(screen, int(x), int(y))
    pyautogui.moveTo(int(x), int(y), duration=max(0.0, float(duration)))


def direction_to_delta(direction: str, distance: int) -> Tuple[int, int]:
    direction = direction.lower()
    if direction == "right":
        return distance, 0
    if direction == "left":
        return -distance, 0
    if direction == "down":
        return 0, distance
    if direction == "up":
        return 0, -distance
    raise ValueError("--direction must be one of: left, right, up, down")


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


def make_result(action: str, screen: Screen, before: Point, after: Point, extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "ok": True,
        "action": action,
        "screen": asdict(screen),
        "position_before": asdict(before),
        "position_after": asdict(after),
    }
    if extra:
        result.update(extra)
    return result


def emit(result: Dict[str, Any], use_json: bool) -> None:
    if use_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"ok: {result.get('ok')} action: {result.get('action')}")
        if "screen" in result:
            screen = result["screen"]
            print(
                f"screen: {screen['width']}x{screen['height']} "
                f"at left={screen['left']} top={screen['top']}"
            )
        if "position_after" in result:
            print(f"position: x={result['position_after']['x']} y={result['position_after']['y']}")


def fail(message: str, use_json: bool) -> int:
    if use_json:
        print(json.dumps({"ok": False, "error": message}, ensure_ascii=False, indent=2), file=sys.stderr)
    else:
        print(f"error: {message}", file=sys.stderr)
    return 1


def run(args: argparse.Namespace) -> int:
    try:
        pyautogui = load_pyautogui()
        screen, before = get_screen_and_position(pyautogui)

        if args.command == "self-check":
            after_screen, after = get_screen_and_position(pyautogui)
            emit(
                make_result(
                    "self-check",
                    after_screen,
                    before,
                    after,
                    {"pyautogui_available": True, "failsafe_enabled": bool(pyautogui.FAILSAFE)},
                ),
                args.json,
            )
            return 0

        if args.command == "position":
            emit(make_result("position", screen, before, before), args.json)
            return 0

        if args.command == "move-to":
            validate_coordinate(screen, args.x, args.y)
            pyautogui.moveTo(args.x, args.y, duration=max(0.0, args.duration))
            _, after = get_screen_and_position(pyautogui)
            emit(make_result("move-to", screen, before, after, {"target": {"x": args.x, "y": args.y}}), args.json)
            return 0

        if args.command == "slide":
            dx = args.dx
            dy = args.dy
            if args.direction is not None or args.distance is not None:
                if args.direction is None or args.distance is None:
                    raise ValueError("use both --direction and --distance together")
                if args.dx is not None or args.dy is not None:
                    raise ValueError("choose either --dx/--dy or --direction/--distance, not both")
                dx, dy = direction_to_delta(args.direction, int(args.distance))
            if dx is None:
                dx = 0
            if dy is None:
                dy = 0
            target_x = before.x + int(dx)
            target_y = before.y + int(dy)
            validate_coordinate(screen, target_x, target_y)
            pyautogui.moveRel(int(dx), int(dy), duration=max(0.0, args.duration))
            _, after = get_screen_and_position(pyautogui)
            emit(make_result("slide", screen, before, after, {"delta": {"dx": int(dx), "dy": int(dy)}}), args.json)
            return 0

        if args.command == "scroll":
            maybe_move_to(pyautogui, screen, args.x, args.y, args.duration)
            if int(args.amount) <= 0:
                raise ValueError("--amount must be a positive integer")
            clicks = int(args.amount)
            if args.direction == "down":
                clicks = -abs(clicks)
            elif args.direction == "up":
                clicks = abs(clicks)
            else:
                raise ValueError("--direction must be one of: up, down")
            pyautogui.scroll(clicks)
            _, after = get_screen_and_position(pyautogui)
            emit(make_result("scroll", screen, before, after, {"scroll": {"direction": args.direction, "amount": int(args.amount), "pyautogui_clicks": clicks}}), args.json)
            return 0

        if args.command == "left-click":
            maybe_move_to(pyautogui, screen, args.x, args.y, args.duration)
            pyautogui.click(button="left")
            _, after = get_screen_and_position(pyautogui)
            emit(make_result("left-click", screen, before, after), args.json)
            return 0

        if args.command == "right-click":
            maybe_move_to(pyautogui, screen, args.x, args.y, args.duration)
            pyautogui.click(button="right")
            _, after = get_screen_and_position(pyautogui)
            emit(make_result("right-click", screen, before, after), args.json)
            return 0

        if args.command == "left-down":
            maybe_move_to(pyautogui, screen, args.x, args.y, args.duration)
            pyautogui.mouseDown(button="left")
            _, after = get_screen_and_position(pyautogui)
            emit(make_result("left-down", screen, before, after), args.json)
            return 0

        if args.command == "left-up":
            maybe_move_to(pyautogui, screen, args.x, args.y, args.duration)
            pyautogui.mouseUp(button="left")
            _, after = get_screen_and_position(pyautogui)
            emit(make_result("left-up", screen, before, after), args.json)
            return 0

        if args.command == "left-hold":
            maybe_move_to(pyautogui, screen, args.x, args.y, args.duration)
            pyautogui.mouseDown(button="left")
            try:
                time.sleep(args.seconds)
            finally:
                pyautogui.mouseUp(button="left")
            _, after = get_screen_and_position(pyautogui)
            emit(make_result("left-hold", screen, before, after, {"held_seconds": args.seconds}), args.json)
            return 0

        raise ValueError(f"unknown command: {args.command}")
    except Exception as exc:
        return fail(str(exc), getattr(args, "json", False))


def add_common_action_args(parser: argparse.ArgumentParser, include_xy: bool = True) -> None:
    if include_xy:
        parser.add_argument("--x", type=int, default=None, help="Optional absolute x coordinate to move to before the action.")
        parser.add_argument("--y", type=int, default=None, help="Optional absolute y coordinate to move to before the action.")
    parser.add_argument("--duration", type=nonnegative_float, default=0.0, help="Mouse movement duration in seconds.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Control the local mouse pointer for Claude Code GUI automation.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    p = subparsers.add_parser("self-check", help="Check pyautogui access, screen size, and current mouse position.")
    p.add_argument("--json", action="store_true")

    p = subparsers.add_parser("position", help="Return the current mouse position and screen size.")
    p.add_argument("--json", action="store_true")

    p = subparsers.add_parser("move-to", help="Move the cursor to an absolute x/y coordinate.")
    p.add_argument("--x", type=int, required=True)
    p.add_argument("--y", type=int, required=True)
    p.add_argument("--duration", type=nonnegative_float, default=0.0)
    p.add_argument("--json", action="store_true")

    p = subparsers.add_parser("slide", help="Slide the cursor by dx/dy or by direction plus distance.")
    p.add_argument("--dx", type=int, default=None, help="Relative x movement. Positive means right, negative means left.")
    p.add_argument("--dy", type=int, default=None, help="Relative y movement. Positive means down, negative means up.")
    p.add_argument("--direction", choices=["left", "right", "up", "down"], default=None)
    p.add_argument("--distance", type=positive_int, default=None)
    p.add_argument("--duration", type=nonnegative_float, default=0.0)
    p.add_argument("--json", action="store_true")

    p = subparsers.add_parser("scroll", help="Scroll the mouse wheel up or down at the current position or after moving to x/y.")
    add_common_action_args(p)
    p.add_argument("--direction", choices=["up", "down"], required=True, help="Scroll direction.")
    p.add_argument("--amount", type=positive_int, required=True, help="Scroll amount in wheel clicks/steps. Use a small value first, such as 3 to 8.")

    p = subparsers.add_parser("left-click", help="Left-click at current position or after moving to x/y.")
    add_common_action_args(p)

    p = subparsers.add_parser("right-click", help="Right-click at current position or after moving to x/y.")
    add_common_action_args(p)

    p = subparsers.add_parser("left-down", help="Press and hold the left mouse button.")
    add_common_action_args(p)

    p = subparsers.add_parser("left-up", help="Release the left mouse button.")
    add_common_action_args(p)

    p = subparsers.add_parser("left-hold", help="Press the left mouse button, wait, then release.")
    add_common_action_args(p)
    p.add_argument("--seconds", type=nonnegative_float, default=1.0, help="How long to hold the left button before releasing.")

    return parser


def main() -> int:
    configure_utf8_stdio()
    parser = build_parser()
    args = parser.parse_args()
    return run(args)


if __name__ == "__main__":
    raise SystemExit(main())
