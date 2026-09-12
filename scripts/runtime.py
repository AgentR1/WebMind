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
    return Path.home() / 'Library' / 'Application Support' / 'WebMindCodex'


def data_dir(root: Path = ROOT) -> Path:
    if os.environ.get('WEBMIND_CODEX_DATA_DIR') or os.environ.get('WEBMIND_DATA_DIR'):
        return default_data_dir()
    configured = load_settings(root).get('data_dir')
    return Path(configured).expanduser().resolve() if configured else default_data_dir()


def venv_python(data: Path) -> Path:
    return data / '.venv' / ('bin/python')




def require_native_host() -> None:
    if sys.version_info < MINIMUM_PYTHON:
        raise RuntimeError('webmind-codex requires Python 3.10 or newer.')
    if platform.system() != 'Darwin':
        raise RuntimeError('This edition requires a native macOS desktop and native macOS Python; cloud and remote desktops are not supported.')




def native_desktop_geometry() -> dict[str, Any]:
    """Read macOS native desktop input coordinates."""
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




def gui_preflight(component: str) -> None:
    """Fail closed on a denied macOS desktop operation."""
    require_native_host()
    status = macos_permissions()
    permission = 'screen_recording' if component == 'screenshot' else 'accessibility'
    if status.get(permission) is False:
        raise RuntimeError(f'macOS {permission} permission is missing. {status["help"]}')
