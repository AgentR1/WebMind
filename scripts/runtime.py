"""Shared, dependency-free paths and host diagnostics for webmind-codex."""
from __future__ import annotations

import ctypes
import json
import os
import platform
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MINIMUM_PYTHON = (3, 10)
INSTALL_MARKER = '.webmind-install.json'


def configure_utf8_stdio() -> None:
    for name in ('stdin', 'stdout', 'stderr'):
        method = getattr(getattr(sys, name), 'reconfigure', None)
        if callable(method):
            try:
                method(encoding='utf-8', errors='strict')
            except (OSError, ValueError):
                pass


def load_settings(root: Path = ROOT) -> dict[str, Any]:
    path = root / INSTALL_MARKER
    if not path.is_file():
        return {}
    data = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(data, dict) or data.get('name') != 'webmind-codex':
        raise ValueError(f'Invalid webmind-codex installation metadata: {path}')
    return data


def default_data_dir() -> Path:
    override = os.environ.get('WEBMIND_CODEX_DATA_DIR') or os.environ.get('WEBMIND_DATA_DIR')
    if override:
        return Path(override).expanduser().resolve()
    base = os.environ.get('LOCALAPPDATA')
    return (Path(base) if base else Path.home() / 'AppData' / 'Local') / 'WebMindCodex'


def data_dir(root: Path = ROOT) -> Path:
    if os.environ.get('WEBMIND_CODEX_DATA_DIR') or os.environ.get('WEBMIND_DATA_DIR'):
        return default_data_dir()
    configured = load_settings(root).get('data_dir')
    return Path(configured).expanduser().resolve() if configured else default_data_dir()


def venv_python(data: Path) -> Path:
    return data / '.venv' / ('Scripts/python.exe')


def is_wsl() -> bool:
    return platform.system() == 'Linux' and (
        'microsoft' in platform.release().lower() or bool(os.environ.get('WSL_DISTRO_NAME'))
    )


def require_native_host() -> None:
    if sys.version_info < MINIMUM_PYTHON:
        raise RuntimeError('webmind-codex requires Python 3.10 or newer.')
    if platform.system() != 'Windows':
        raise RuntimeError('This edition requires native Windows PowerShell and native Windows Python; WSL, cloud and remote desktops are not supported.')


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
    rect = dict(zip(('left', 'top', 'width', 'height'), (int(user32.GetSystemMetrics(i)) for i in (76, 77, 78, 79))))
    if rect['width'] <= 0 or rect['height'] <= 0:
        raise RuntimeError('No interactive virtual desktop is available.')
    return {'rect': rect, 'monitors': [], 'coordinate_space': 'windows-physical-pixels'}




def windows_desktop() -> dict[str, Any]:
    """Detect a private/sandbox desktop without switching to another desktop."""
    from ctypes import wintypes
    user32 = ctypes.WinDLL('user32', use_last_error=True)
    kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
    get_info = user32.GetUserObjectInformationW
    get_info.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(wintypes.DWORD)]
    get_info.restype = wintypes.BOOL
    user32.GetThreadDesktop.argtypes = [wintypes.DWORD]
    user32.GetThreadDesktop.restype = wintypes.HANDLE
    user32.GetProcessWindowStation.restype = wintypes.HANDLE
    kernel32.GetCurrentThreadId.restype = wintypes.DWORD
    def name(handle: int) -> str:
        required = wintypes.DWORD()
        get_info(handle, 2, None, 0, ctypes.byref(required))  # UOI_NAME
        if not required.value:
            raise ctypes.WinError(ctypes.get_last_error())
        buffer = ctypes.create_unicode_buffer(required.value // ctypes.sizeof(ctypes.c_wchar) + 1)
        if not get_info(handle, 2, buffer, ctypes.sizeof(buffer), ctypes.byref(required)):
            raise ctypes.WinError(ctypes.get_last_error())
        return buffer.value
    desktop = name(user32.GetThreadDesktop(kernel32.GetCurrentThreadId()))
    station = name(user32.GetProcessWindowStation())
    return {'desktop': desktop, 'window_station': station,
            'interactive_default_desktop': desktop.lower() == 'default' and station.lower() == 'winsta0',
            'help': 'GUI commands need the signed-in user desktop. Request a narrowly scoped, user-approved host command when Codex runs on a private sandbox desktop. Do not change sandbox settings automatically.'}


def gui_preflight(component: str) -> None:
    """Fail closed on a denied Windows desktop operation."""
    require_native_host()
    status = windows_desktop()
    if not status['interactive_default_desktop']:
        raise RuntimeError(f'Not on the interactive Windows desktop ({status["window_station"]}/{status["desktop"]}). {status["help"]}')
