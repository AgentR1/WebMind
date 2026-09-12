"""Shared desktop-coordinate helpers for webmind-claudecode."""
from __future__ import annotations

import ctypes
import platform
from typing import Any


def prepare_windows_dpi() -> None:
    """Set physical-pixel coordinates before importing a GUI library."""
    try:
        if ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4)):
            return
    except (AttributeError, OSError):
        pass
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except (AttributeError, OSError):
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except (AttributeError, OSError):
            pass


def native_desktop_geometry() -> dict[str, Any]:
    """Read Windows native desktop input coordinates."""
    prepare_windows_dpi()
    user32 = ctypes.windll.user32
    rect = dict(
        zip(
            ("left", "top", "width", "height"),
            (int(user32.GetSystemMetrics(i)) for i in (76, 77, 78, 79)),
        )
    )
    if rect["width"] <= 0 or rect["height"] <= 0:
        raise RuntimeError("No interactive virtual desktop is available.")
    return {"rect": rect, "monitors": [], "coordinate_space": "windows-physical-pixels"}
