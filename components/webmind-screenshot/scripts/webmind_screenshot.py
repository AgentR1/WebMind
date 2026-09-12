#!/usr/bin/env python3
"""
Read the current desktop resolution and capture screenshots.

This single program supports four screen tasks:
  1. resolution: read current virtual desktop bounds only
  2. full:       capture the full virtual desktop
  3. half:       capture the left or right half of the virtual desktop
  4. region:     capture a custom rectangle from x1,y1 to x2,y2

Important: every screenshot command reads the current resolution first, then computes
and captures the requested region from that live desktop metadata.
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# Resolve shared helpers relative to this source file, never the shell cwd.
from pathlib import Path as _Path
_shared = str(_Path(__file__).resolve().parents[3] / "scripts")
if _shared not in sys.path:
    sys.path.insert(0, _shared)
from runtime import prepare_windows_dpi, native_desktop_geometry
prepare_windows_dpi()


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


@dataclass(frozen=True)
class Rect:
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

    def to_dict(self) -> Dict[str, int]:
        return {
            "left": self.left,
            "top": self.top,
            "width": self.width,
            "height": self.height,
            "right": self.right,
            "bottom": self.bottom,
        }


@dataclass(frozen=True)
class DesktopInfo:
    backend: str
    rect: Rect
    monitors: List[Dict[str, int]]

    def to_dict(self) -> Dict[str, Any]:
        data = self.rect.to_dict()
        data.update(
            {
                "backend": self.backend,
                "resolution": f"{self.rect.width}x{self.rect.height}",
                "monitors": self.monitors,
            }
        )
        return data


def _timestamp_name(prefix: str) -> str:
    return datetime.now().strftime(f"{prefix}_%Y%m%d_%H%M%S.png")


def _ensure_output_path(output: Optional[str], prefix: str) -> Path:
    path = Path(output) if output else Path.cwd() / _timestamp_name(prefix)
    if path.suffix.lower() != ".png":
        path = path.with_suffix(".png")
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _open_mss(*, with_cursor: bool = False):
    """Open mss with optional native cursor capture across mss versions."""
    import mss  # type: ignore

    factory = getattr(mss, "MSS", None) or getattr(mss, "mss", None)
    if factory is None:
        raise RuntimeError("installed mss package exposes neither MSS nor mss")

    try:
        return factory(with_cursor=with_cursor)
    except TypeError:
        # Older releases did not accept with_cursor in the constructor but may
        # still expose it as a writable instance property.
        instance = factory()
        if hasattr(instance, "with_cursor"):
            instance.with_cursor = with_cursor
            return instance
        if not with_cursor:
            return instance
        try:
            instance.close()
        except Exception:
            pass
        raise RuntimeError(
            "installed mss version does not support mouse cursor capture; "
            "upgrade webmind-codex dependencies with the plugin installer"
        )


def _read_resolution_with_mss() -> DesktopInfo:
    with _open_mss() as sct:
        monitor = sct.monitors[0]
        rect = Rect(
            left=int(monitor.get("left", 0)),
            top=int(monitor.get("top", 0)),
            width=int(monitor["width"]),
            height=int(monitor["height"]),
        )
        monitors = [
            {
                "left": int(m.get("left", 0)),
                "top": int(m.get("top", 0)),
                "width": int(m.get("width", 0)),
                "height": int(m.get("height", 0)),
            }
            for m in sct.monitors[1:]
        ]
        return DesktopInfo(backend="mss", rect=rect, monitors=monitors)


def _read_resolution_with_pillow() -> DesktopInfo:
    geometry = native_desktop_geometry()
    return DesktopInfo(backend="native_geometry", rect=Rect(**geometry["rect"]), monitors=geometry["monitors"])




def read_resolution() -> DesktopInfo:
    errors: List[str] = []
    for label, func in (
        ("mss", _read_resolution_with_mss),
        ("pillow_imagegrab", _read_resolution_with_pillow),
    ):
        try:
            return func()
        except Exception as exc:
            errors.append(f"{label}: {exc}")


    raise RuntimeError(
        "Unable to read screen resolution. Install dependencies with "
        "the webmind-codex project installer, make sure a graphical session is active, "
        "and grant screen-recording permissions if required. Attempts: "
        + " | ".join(errors)
    )


def _capture_rect_with_mss(rect: Rect, output_path: Path, *, with_cursor: bool = True) -> Tuple[str, bool]:
    import mss.tools  # type: ignore

    monitor = {
        "left": rect.left,
        "top": rect.top,
        "width": rect.width,
        "height": rect.height,
    }
    # mss currently implements native cursor compositing on Linux. Passing the
    # option on other platforms is ignored and emits a deprecation warning, so
    # those platforms use the explicit system-position overlay below.
    request_native_cursor = False
    with _open_mss(with_cursor=request_native_cursor) as sct:
        img = sct.grab(monitor)
        mss.tools.to_png(img.rgb, img.size, output=str(output_path))
        native_cursor_included = request_native_cursor and bool(getattr(sct, "with_cursor", False))
    return "mss", native_cursor_included


def _capture_rect_with_pillow(rect: Rect, output_path: Path) -> str:
    from PIL import ImageGrab  # type: ignore

    box = (rect.left, rect.top, rect.right, rect.bottom)
    # Supplying the absolute bbox directly avoids treating a negative virtual
    # desktop origin as an offset into an already captured image.
    img = ImageGrab.grab(bbox=box, all_screens=True)
    img.save(output_path)
    return "pillow_imagegrab"




def capture_rect(rect: Rect, output_path: Path, *, with_cursor: bool = True) -> Tuple[str, bool]:
    errors: List[str] = []
    try:
        return _capture_rect_with_mss(rect, output_path, with_cursor=with_cursor)
    except Exception as exc:
        errors.append(f"mss: {exc}")

    try:
        return _capture_rect_with_pillow(rect, output_path), False
    except Exception as exc:
        errors.append(f"pillow_imagegrab: {exc}")


    raise RuntimeError(
        "Unable to capture screenshot. Install dependencies with "
        "the webmind-codex project installer, make sure a graphical session is active, "
        "and grant screen-recording permissions if required. Attempts: "
        + " | ".join(errors)
    )


def _read_pointer_position() -> Tuple[int, int]:
    """Return the current pointer position in absolute desktop coordinates."""
    errors: List[str] = []
    import ctypes
    from ctypes import wintypes

    class Point(ctypes.Structure):
        _fields_ = [("x", wintypes.LONG), ("y", wintypes.LONG)]

    try:
        user32 = ctypes.WinDLL("user32", use_last_error=True)
        user32.GetCursorPos.argtypes = [ctypes.POINTER(Point)]
        user32.GetCursorPos.restype = wintypes.BOOL
        point = Point()
        if user32.GetCursorPos(ctypes.byref(point)):
            return int(point.x), int(point.y)
        errors.append(f"win32: {ctypes.WinError(ctypes.get_last_error())}")
    except Exception as exc:
        errors.append(f"win32: {exc}")

    try:
        import pyautogui  # type: ignore

        point = pyautogui.position()
        return int(point[0]), int(point[1])
    except Exception as exc:
        errors.append(f"pyautogui: {exc}")
        raise RuntimeError(
            "cannot read mouse pointer position on this platform; install pyautogui "
            "or use --no-cursor. Attempts: " + " | ".join(errors)
        ) from exc


def _overlay_cursor_marker(
    output_path: Path,
    region: Rect,
    pointer_position: Optional[Tuple[int, int]] = None,
) -> Dict[str, Any]:
    """Draw a cursor-shaped marker whose tip is the live system pointer."""
    x, y = pointer_position if pointer_position is not None else _read_pointer_position()
    result: Dict[str, Any] = {
        "requested": True,
        "included": False,
        "source": "system-position-overlay",
        "position": {"x": x, "y": y, "coordinate_space": "desktop-absolute-pixels"},
    }
    if not (region.left <= x < region.right and region.top <= y < region.bottom):
        result["reason"] = "outside-capture-region"
        return result

    from PIL import Image, ImageDraw  # type: ignore

    with Image.open(output_path) as original:
        image = original.convert("RGBA")
    scale_x = image.width / region.width
    scale_y = image.height / region.height
    image_x = round((x - region.left) * scale_x)
    image_y = round((y - region.top) * scale_y)

    scale = max(1.0, min(scale_x, scale_y))
    points = [(0, 0), (0, 25), (7, 19), (13, 32), (18, 29), (12, 17), (25, 17)]
    points = [
        (image_x + round(point_x * scale), image_y + round(point_y * scale))
        for point_x, point_y in points
    ]
    draw = ImageDraw.Draw(image)
    draw.polygon(points, fill="#111827")
    draw.line(points + [points[0]], fill="white", width=max(2, round(2 * scale)), joint="curve")
    image.save(output_path, format="PNG")

    result.update(
        {
            "included": True,
            "image_point": {"x": image_x, "y": image_y},
            "kind": "pointer-marker",
            "reason": None,
        }
    )
    return result


def _validate_inside_desktop(region: Rect, desktop: Rect) -> None:
    if region.width <= 0 or region.height <= 0:
        raise ValueError("Capture region must have positive width and height.")
    if (
        region.left < desktop.left
        or region.top < desktop.top
        or region.right > desktop.right
        or region.bottom > desktop.bottom
    ):
        raise ValueError(
            "Capture region is outside current desktop bounds. "
            f"region={region.to_dict()} desktop={desktop.to_dict()}"
        )


def _full_region(desktop: Rect) -> Rect:
    return desktop


def _half_region(desktop: Rect, side: str) -> Rect:
    left_width = desktop.width // 2
    right_width = desktop.width - left_width
    if side == "left":
        return Rect(desktop.left, desktop.top, left_width, desktop.height)
    if side == "right":
        return Rect(desktop.left + left_width, desktop.top, right_width, desktop.height)
    raise ValueError("side must be 'left' or 'right'")


def _custom_region(x1: int, y1: int, x2: int, y2: int) -> Rect:
    if x2 <= x1:
        raise ValueError("x2 must be greater than x1.")
    if y2 <= y1:
        raise ValueError("y2 must be greater than y1.")
    return Rect(left=x1, top=y1, width=x2 - x1, height=y2 - y1)


def _base_result(task: str, desktop_info: DesktopInfo) -> Dict[str, Any]:
    return {
        "ok": True,
        "task": task,
        "resolution": f"{desktop_info.rect.width}x{desktop_info.rect.height}",
        "width": desktop_info.rect.width,
        "height": desktop_info.rect.height,
        "left": desktop_info.rect.left,
        "top": desktop_info.rect.top,
        "right": desktop_info.rect.right,
        "bottom": desktop_info.rect.bottom,
        "desktop": desktop_info.rect.to_dict(),
        "desktop_coordinate_space": "desktop-absolute-pixels",
        "backend": desktop_info.backend,
        "monitors": desktop_info.monitors,
    }


def _print_result(result: Dict[str, Any], as_json: bool) -> None:
    if as_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    task = result.get("task", "unknown")
    print(f"Task: {task}")
    print(f"Resolution: {result.get('resolution')}")
    if "output" in result:
        print(f"Screenshot saved: {result['output']}")
        print(f"Captured region: {result.get('region')}")
    print(f"Backend: {result.get('backend')}")


def _self_check(as_json: bool) -> int:
    result: Dict[str, Any] = {
        "ok": True,
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "cwd": os.getcwd(),
        "mss_available": False,
        "pillow_available": False,
    }
    try:
        import mss  # noqa: F401

        result["mss_available"] = True
    except Exception:
        pass
    try:
        from PIL import ImageGrab  # noqa: F401

        result["pillow_available"] = True
    except Exception:
        pass

    result["ok"] = bool(
        result["mss_available"]
        or result["pillow_available"]
    )
    if not result["ok"]:
        result["error"] = "no supported screenshot backend is available"

    _print_result(result, as_json)
    return 0 if result["ok"] else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Read screen resolution first, then capture full, half, or custom desktop screenshots."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_check = sub.add_parser("self-check", help="Check dependency availability without taking a screenshot.")
    p_check.add_argument("--json", action="store_true", help="Print machine-readable JSON.")

    p_res = sub.add_parser("resolution", help="Read the current virtual desktop resolution only.")
    p_res.add_argument("--json", action="store_true", help="Print machine-readable JSON.")

    p_full = sub.add_parser("full", help="Capture the full virtual desktop.")
    p_full.add_argument("--output", "-o", help="Output PNG path. Defaults to screenshot_full_TIMESTAMP.png.")
    p_full.add_argument("--no-cursor", action="store_true", help="Do not include the mouse pointer in the screenshot.")
    p_full.add_argument("--json", action="store_true", help="Print machine-readable JSON.")

    p_half = sub.add_parser("half", help="Capture the left or right half of the virtual desktop.")
    p_half.add_argument("--side", choices=("left", "right"), required=True, help="Half of the screen to capture.")
    p_half.add_argument("--output", "-o", help="Output PNG path. Defaults to screenshot_half_SIDE_TIMESTAMP.png.")
    p_half.add_argument("--no-cursor", action="store_true", help="Do not include the mouse pointer in the screenshot.")
    p_half.add_argument("--json", action="store_true", help="Print machine-readable JSON.")

    p_region = sub.add_parser("region", help="Capture a custom rectangle from x1,y1 to x2,y2.")
    p_region.add_argument("--x1", type=int, required=True, help="Left x coordinate.")
    p_region.add_argument("--y1", type=int, required=True, help="Top y coordinate.")
    p_region.add_argument("--x2", type=int, required=True, help="Right x coordinate; must be greater than x1.")
    p_region.add_argument("--y2", type=int, required=True, help="Bottom y coordinate; must be greater than y1.")
    p_region.add_argument("--output", "-o", help="Output PNG path. Defaults to screenshot_region_TIMESTAMP.png.")
    p_region.add_argument("--no-cursor", action="store_true", help="Do not include the mouse pointer in the screenshot.")
    p_region.add_argument("--json", action="store_true", help="Print machine-readable JSON.")

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    configure_utf8_stdio()
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "self-check":
        return _self_check(args.json)

    try:
        # Mandatory behavior: every non-self-check task reads current resolution first.
        desktop_info = read_resolution()
        result = _base_result(args.command, desktop_info)

        if args.command == "resolution":
            _print_result(result, args.json)
            return 0

        if args.command == "full":
            region = _full_region(desktop_info.rect)
            output_path = _ensure_output_path(args.output, "screenshot_full")
        elif args.command == "half":
            region = _half_region(desktop_info.rect, args.side)
            output_path = _ensure_output_path(args.output, f"screenshot_half_{args.side}")
            result["side"] = args.side
        elif args.command == "region":
            region = _custom_region(args.x1, args.y1, args.x2, args.y2)
            output_path = _ensure_output_path(args.output, "screenshot_region")
        else:
            parser.error(f"Unknown command: {args.command}")
            return 2

        _validate_inside_desktop(region, desktop_info.rect)
        cursor_requested = not args.no_cursor
        pointer_position: Optional[Tuple[int, int]] = None
        pointer_error: Optional[str] = None
        if cursor_requested:
            try:
                # Sample before capture so the marker describes the captured
                # moment instead of a later pointer position.
                pointer_position = _read_pointer_position()
            except Exception as exc:
                pointer_error = str(exc)
        capture_backend, native_cursor_included = capture_rect(
            region, output_path, with_cursor=cursor_requested
        )
        if not cursor_requested:
            cursor: Dict[str, Any] = {
                "requested": False,
                "included": False,
                "source": None,
                "reason": "disabled",
            }
        elif native_cursor_included:
            cursor = {
                "requested": True,
                "included": True,
                "source": "mss-native",
                "reason": None,
            }
        else:
            try:
                if pointer_position is None:
                    raise RuntimeError(pointer_error or "pointer position unavailable")
                cursor = _overlay_cursor_marker(output_path, region, pointer_position)
            except Exception as exc:
                cursor = {
                    "requested": True,
                    "included": False,
                    "source": "system-position-overlay",
                    "reason": "cursor-overlay-failed",
                    "error": str(exc),
                }
        result.update(
            {
                "output": str(output_path.resolve()),
                "region": region.to_dict(),
                "capture_backend": capture_backend,
                "cursor": cursor,
            }
        )
        from PIL import Image
        with Image.open(output_path) as image:
            result["image"] = {
                "width": image.width, "height": image.height,
                "scale_x": image.width / region.width,
                "scale_y": image.height / region.height,
                "coordinate_space": "image-pixels",
                "to_desktop": "x = region.left + image_x / scale_x; y = region.top + image_y / scale_y",
            }
        if cursor_requested and not cursor.get("included"):
            result["warnings"] = [
                "Mouse pointer was not included: " + cursor.get("reason", "unavailable")
            ]
        _print_result(result, args.json)
        return 0

    except Exception as exc:
        error = {"ok": False, "task": getattr(args, "command", "unknown"), "error": str(exc)}
        if getattr(args, "json", False):
            print(json.dumps(error, ensure_ascii=False, indent=2), file=sys.stderr)
        else:
            print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
