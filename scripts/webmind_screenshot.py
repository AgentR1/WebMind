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
import shutil
import struct
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


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


def _mss_session():
    import mss  # type: ignore

    factory = getattr(mss, "MSS", None) or mss.mss
    return factory()


def _read_resolution_with_mss() -> DesktopInfo:
    with _mss_session() as sct:
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
    from PIL import ImageGrab  # type: ignore

    img = ImageGrab.grab(all_screens=True)
    width, height = img.size
    return DesktopInfo(
        backend="pillow_imagegrab",
        rect=Rect(left=0, top=0, width=int(width), height=int(height)),
        monitors=[],
    )


def _read_resolution_with_macos_screencapture() -> DesktopInfo:
    # Native fallback. It briefly captures a temporary file because screencapture
    # does not expose resolution directly in a portable JSON-friendly way.
    from tempfile import NamedTemporaryFile

    with NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        tmp_path = Path(tmp.name)
    try:
        subprocess.run(["screencapture", "-x", "-m", str(tmp_path)], check=True)
        from PIL import Image  # type: ignore

        with Image.open(tmp_path) as img:
            width, height = img.size
        return DesktopInfo(
            backend="macos_screencapture",
            rect=Rect(left=0, top=0, width=int(width), height=int(height)),
            monitors=[],
        )
    finally:
        try:
            tmp_path.unlink(missing_ok=True)
        except Exception:
            pass


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

    if platform.system() == "Darwin":
        try:
            return _read_resolution_with_macos_screencapture()
        except Exception as exc:
            errors.append(f"macos_screencapture: {exc}")

    raise RuntimeError(
        "Unable to read screen resolution. Install dependencies with "
        "'python -m pip install -r requirements-desktop.txt', make sure a graphical session is active, "
        "and grant screen-recording permissions if required. Attempts: "
        + " | ".join(errors)
    )


def _capture_rect_with_mss(rect: Rect, output_path: Path) -> str:
    import mss  # type: ignore
    import mss.tools  # type: ignore

    monitor = {
        "left": rect.left,
        "top": rect.top,
        "width": rect.width,
        "height": rect.height,
    }
    with _mss_session() as sct:
        img = sct.grab(monitor)
        mss.tools.to_png(img.rgb, img.size, output=str(output_path))
    return "mss"


def _capture_rect_with_pillow(rect: Rect, output_path: Path) -> str:
    from PIL import ImageGrab  # type: ignore

    img = ImageGrab.grab(all_screens=True)
    # These are coordinates in Pillow's full captured image, not mouse coordinates.
    box = (rect.left, rect.top, rect.right, rect.bottom)
    cropped = img.crop(box)
    cropped.save(output_path)
    return "pillow_imagegrab"


def _capture_rect_with_macos_screencapture(rect: Rect, output_path: Path) -> str:
    # -R uses desktop coordinates that can differ from PNG pixels on Retina.
    # Capture the same primary-display image used for resolution, then crop pixels.
    from tempfile import NamedTemporaryFile
    from PIL import Image  # type: ignore

    with NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        tmp_path = Path(tmp.name)
    try:
        subprocess.run(["screencapture", "-x", "-m", str(tmp_path)], check=True)
        with Image.open(tmp_path) as img:
            img.crop((rect.left, rect.top, rect.right, rect.bottom)).save(output_path)
    finally:
        tmp_path.unlink(missing_ok=True)
    return "macos_screencapture"


def capture_rect(rect: Rect, output_path: Path, backend: Optional[str] = None) -> str:
    backends = {
        "mss": _capture_rect_with_mss,
        "pillow_imagegrab": _capture_rect_with_pillow,
        "macos_screencapture": _capture_rect_with_macos_screencapture,
    }
    if backend is not None:
        # Never silently switch coordinate spaces after choosing a capture region.
        if backend not in backends:
            raise ValueError(f"Unknown screenshot backend: {backend}")
        return backends[backend](rect, output_path)
    errors: List[str] = []
    for label, func in (
        ("mss", _capture_rect_with_mss),
        ("pillow_imagegrab", _capture_rect_with_pillow),
    ):
        try:
            return func(rect, output_path)
        except Exception as exc:
            errors.append(f"{label}: {exc}")

    if platform.system() == "Darwin":
        try:
            return _capture_rect_with_macos_screencapture(rect, output_path)
        except Exception as exc:
            errors.append(f"macos_screencapture: {exc}")

    raise RuntimeError(
        "Unable to capture screenshot. Install dependencies with "
        "'python -m pip install -r requirements-desktop.txt', make sure a graphical session is active, "
        "and grant screen-recording permissions if required. Attempts: "
        + " | ".join(errors)
    )


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
        "backend": desktop_info.backend,
        "monitors": desktop_info.monitors,
        "coordinate_space": "mss_virtual_desktop" if desktop_info.backend == "mss" else "captured_image_pixels",
        "capture_scope": "primary_display" if desktop_info.backend == "macos_screencapture" else "backend_desktop",
        "mouse_mapping_verified": False,
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
        "macos_screencapture_available": False,
        "task": "self-check",
        "runtime_access_checked": False,
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
    if platform.system() == "Darwin":
        result["macos_screencapture_available"] = bool(shutil.which("screencapture"))

    result["ok"] = result["mss_available"] or result["pillow_available"]

    _print_result(result, as_json)
    return 0 if result["ok"] else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="WebMind: read screen resolution first, then capture full, half, or custom desktop screenshots."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_check = sub.add_parser("self-check", help="Check dependency availability without taking a screenshot.")
    p_check.add_argument("--json", action="store_true", help="Print machine-readable JSON.")

    p_res = sub.add_parser("resolution", help="Read the current virtual desktop resolution only.")
    p_res.add_argument("--json", action="store_true", help="Print machine-readable JSON.")

    p_full = sub.add_parser("full", help="Capture the full virtual desktop.")
    p_full.add_argument("--output", "-o", help="Output PNG path. Defaults to screenshot_full_TIMESTAMP.png.")
    p_full.add_argument("--json", action="store_true", help="Print machine-readable JSON.")

    p_half = sub.add_parser("half", help="Capture the left or right half of the virtual desktop.")
    p_half.add_argument("--side", choices=("left", "right"), required=True, help="Half of the screen to capture.")
    p_half.add_argument("--output", "-o", help="Output PNG path. Defaults to screenshot_half_SIDE_TIMESTAMP.png.")
    p_half.add_argument("--json", action="store_true", help="Print machine-readable JSON.")

    p_region = sub.add_parser("region", help="Capture a custom rectangle from x1,y1 to x2,y2.")
    p_region.add_argument("--x1", type=int, required=True, help="Left x coordinate.")
    p_region.add_argument("--y1", type=int, required=True, help="Top y coordinate.")
    p_region.add_argument("--x2", type=int, required=True, help="Right x coordinate; must be greater than x1.")
    p_region.add_argument("--y2", type=int, required=True, help="Bottom y coordinate; must be greater than y1.")
    p_region.add_argument("--output", "-o", help="Output PNG path. Defaults to screenshot_region_TIMESTAMP.png.")
    p_region.add_argument("--json", action="store_true", help="Print machine-readable JSON.")

    return parser


def main(argv: Optional[List[str]] = None) -> int:
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
            prefix = "screenshot_full"
        elif args.command == "half":
            region = _half_region(desktop_info.rect, args.side)
            prefix = f"screenshot_half_{args.side}"
            result["side"] = args.side
        elif args.command == "region":
            region = _custom_region(args.x1, args.y1, args.x2, args.y2)
            prefix = "screenshot_region"
        else:
            parser.error(f"Unknown command: {args.command}")
            return 2

        _validate_inside_desktop(region, desktop_info.rect)
        output_path = _ensure_output_path(args.output, prefix)
        capture_backend = capture_rect(region, output_path, backend=desktop_info.backend)
        with output_path.open("rb") as image:
            header = image.read(24)
        if len(header) < 24 or header[:8] != b"\x89PNG\r\n\x1a\n" or header[12:16] != b"IHDR":
            raise RuntimeError("Screenshot backend did not produce a PNG image")
        image_width, image_height = struct.unpack(">II", header[16:24])
        result.update(
            {
                "output": str(output_path.resolve()),
                "region": region.to_dict(),
                "capture_backend": capture_backend,
                "image": {"width": image_width, "height": image_height},
            }
        )
        _print_result(result, args.json)
        return 0

    except Exception as exc:
        error = {"ok": False, "task": getattr(args, "command", "unknown"), "error": str(exc)}
        if getattr(args, "json", False):
            print(json.dumps(error, ensure_ascii=False, indent=2))
        else:
            print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
