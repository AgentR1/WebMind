"""Shared, dependency-free paths and host diagnostics for WebUse for Codex."""
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
INSTALL_MARKER = '.webuse-install.json'


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
    if not isinstance(data, dict) or data.get('name') != 'webuse-codex':
        raise ValueError(f'Invalid WebUse installation metadata: {path}')
    return data


def default_data_dir() -> Path:
    override = os.environ.get('WEBUSE_CODEX_DATA_DIR') or os.environ.get('WEBUSE_DATA_DIR')
    if override:
        return Path(override).expanduser().resolve()
    if platform.system() == 'Windows':
        base = os.environ.get('LOCALAPPDATA')
        return (Path(base) if base else Path.home() / 'AppData' / 'Local') / 'WebUseCodex'
    if platform.system() == 'Darwin':
        return Path.home() / 'Library' / 'Application Support' / 'WebUseCodex'
    return Path(os.environ.get('XDG_DATA_HOME', str(Path.home() / '.local' / 'share'))) / 'webuse-codex'


def data_dir(root: Path = ROOT) -> Path:
    if os.environ.get('WEBUSE_CODEX_DATA_DIR') or os.environ.get('WEBUSE_DATA_DIR'):
        return default_data_dir()
    configured = load_settings(root).get('data_dir')
    return Path(configured).expanduser().resolve() if configured else default_data_dir()


def venv_python(data: Path) -> Path:
    return data / '.venv' / ('Scripts/python.exe' if platform.system() == 'Windows' else 'bin/python')


def is_wsl() -> bool:
    return platform.system() == 'Linux' and (
        'microsoft' in platform.release().lower() or bool(os.environ.get('WSL_DISTRO_NAME'))
    )


def require_native_host() -> None:
    if sys.version_info < MINIMUM_PYTHON:
        raise RuntimeError('WebUse for Codex requires Python 3.10 or newer.')
    if is_wsl():
        raise RuntimeError('WSL cannot control the native Windows desktop with this package. Run Codex and WebUse in native Windows PowerShell.')
    if platform.system() not in {'Windows', 'Darwin'}:
        raise RuntimeError('Desktop automation requires native Windows or macOS. This is not a remote/cloud desktop bridge.')


def prepare_windows_dpi() -> None:
    """Set physical-pixel coordinates before importing a GUI library."""
    if platform.system() != 'Windows':
        return
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
    """Get OS-input coordinates; macOS points are not Retina image pixels."""
    if platform.system() == 'Windows':
        prepare_windows_dpi()
        user32 = ctypes.windll.user32
        rect = dict(zip(('left', 'top', 'width', 'height'), (int(user32.GetSystemMetrics(i)) for i in (76, 77, 78, 79))))
        if rect['width'] <= 0 or rect['height'] <= 0:
            raise RuntimeError('No interactive virtual desktop is available.')
        return {'rect': rect, 'monitors': [], 'coordinate_space': 'windows-physical-pixels'}
    if platform.system() == 'Darwin':
        import Quartz
        error, displays, count = Quartz.CGGetActiveDisplayList(32, None, None)
        if error or not count:
            raise RuntimeError('No active macOS displays are available.')
        monitors = []
        for display in displays[:count]:
            rect = Quartz.CGDisplayBounds(display)
            monitors.append({'left': int(rect.origin.x), 'top': int(rect.origin.y),
                             'width': int(rect.size.width), 'height': int(rect.size.height)})
        left = min(r['left'] for r in monitors)
        top = min(r['top'] for r in monitors)
        right = max(r['left'] + r['width'] for r in monitors)
        bottom = max(r['top'] + r['height'] for r in monitors)
        return {'rect': {'left': left, 'top': top, 'width': right-left, 'height': bottom-top},
                'monitors': monitors, 'coordinate_space': 'macos-logical-points'}
    raise RuntimeError('Native desktop geometry is only implemented for Windows and macOS.')


def macos_permissions() -> dict[str, Any]:
    """Read permissions without prompting or taking a screenshot."""
    info: dict[str, Any] = {'screen_recording': None, 'accessibility': None}
    try:
        quartz = ctypes.CDLL('/System/Library/Frameworks/CoreGraphics.framework/CoreGraphics')
        check = quartz.CGPreflightScreenCaptureAccess
        check.restype = ctypes.c_bool
        check.argtypes = []
        info['screen_recording'] = bool(check())
    except (AttributeError, OSError) as exc:
        info['screen_recording_check_error'] = str(exc)
    try:
        framework = ctypes.CDLL('/System/Library/Frameworks/ApplicationServices.framework/ApplicationServices')
        check = framework.AXIsProcessTrusted
        check.restype = ctypes.c_bool
        check.argtypes = []
        info['accessibility'] = bool(check())
    except (AttributeError, OSError) as exc:
        info['accessibility_check_error'] = str(exc)
    info['help'] = ('Grant Screen Recording and Accessibility to the actual host app/terminal in System Settings > Privacy & Security; restart that app. Never change these permissions automatically.')
    return info


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
    """Fail closed on a known wrong desktop or a denied macOS GUI permission."""
    require_native_host()
    if platform.system() == 'Darwin':
        status = macos_permissions()
        permission = 'screen_recording' if component == 'screenshot' else 'accessibility'
        if status.get(permission) is False:
            raise RuntimeError(f'macOS {permission} permission is missing. {status["help"]}')
    elif platform.system() == 'Windows':
        status = windows_desktop()
        if not status['interactive_default_desktop']:
            raise RuntimeError(f'Not on the interactive Windows desktop ({status["window_station"]}/{status["desktop"]}). {status["help"]}')
