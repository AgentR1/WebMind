"""Shared desktop-coordinate helpers for webmind-claudecode."""
from __future__ import annotations

import ctypes
import platform
from typing import Any




def native_desktop_geometry() -> dict[str, Any]:
    """Read macOS native desktop input coordinates."""
    import Quartz

    error, displays, count = Quartz.CGGetActiveDisplayList(32, None, None)
    if error or not count:
        raise RuntimeError("No active macOS displays are available.")
    monitors = []
    for display in displays[:count]:
        rect = Quartz.CGDisplayBounds(display)
        monitors.append(
            {
                "left": int(rect.origin.x),
                "top": int(rect.origin.y),
                "width": int(rect.size.width),
                "height": int(rect.size.height),
            }
        )
    left = min(r["left"] for r in monitors)
    top = min(r["top"] for r in monitors)
    right = max(r["left"] + r["width"] for r in monitors)
    bottom = max(r["top"] + r["height"] for r in monitors)
    return {
        "rect": {"left": left, "top": top, "width": right - left, "height": bottom - top},
        "monitors": monitors,
        "coordinate_space": "macos-logical-points",
    }
