#!/usr/bin/env python3
"""Codex-native dispatcher for the retained webmind-codex components."""
from __future__ import annotations
import argparse
import importlib.util
import json
import os
import platform
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any
from runtime import (ROOT, configure_utf8_stdio, data_dir, venv_python, MINIMUM_PYTHON,
                     require_native_host, macos_permissions, gui_preflight)

COMPONENTS = {
    'cdp': ROOT / 'components/webmind-cdp/scripts/webmind_cdp.py',
    'screenshot': ROOT / 'components/webmind-screenshot/scripts/webmind_screenshot.py',
    'mouse': ROOT / 'components/webmind-mouse-control/scripts/webmind_mouse_control.py',
    'typing': ROOT / 'components/webmind-typing/scripts/webmind_typing.py',
    'mem': ROOT / 'components/webmind-mem/scripts/webmind_mem.py',
    'wait': ROOT / 'scripts/webmind_wait.py',
}
MEM_LOCATION_FILE = ROOT / 'components/webmind-mem/mem-location.json'
INIT_MEM_COMMANDS = {'init-status', 'scan', 'name-info', 'self-check', 'init'}

INPUT_FLAGS = {
    'cdp': {'eval': '--expression-stdin', 'fill': '--text-stdin', 'insert-text': '--text-stdin',
            'launch': '--url-stdin', 'navigate': '--url-stdin'},
    'mem': {'record': '--stdin', 'rewrite': '--stdin', 'record-global': '--stdin', 'rewrite-global': '--stdin'},
    'typing': {'type': '--stdin'},
}


def prepare_input(component: str, arguments: list[str]) -> tuple[list[str], bytes | None]:
    """File input preserves UTF-8 text without shell quoting ambiguity."""
    arguments = list(arguments)
    if '--input-file' not in arguments:
        return arguments, None
    if arguments.count('--input-file') != 1:
        raise ValueError('--input-file can be specified only once')
    index = arguments.index('--input-file')
    if index + 1 >= len(arguments):
        raise ValueError('--input-file requires a UTF-8 filename')
    path = Path(arguments[index + 1]).expanduser()
    del arguments[index:index + 2]
    # Match the subcommand after parsing global options, not inside their values.
    if component == 'cdp':
        sub = _cdp_command(arguments)
    elif component == 'mem':
        sub = next((arg for arg in arguments if arg in INPUT_FLAGS['mem']), '')
    else:
        sub = arguments[0] if arguments else ''
    flag = INPUT_FLAGS.get(component, {}).get(sub)
    if not flag:
        raise ValueError('--input-file is supported only for text-taking CDP, memory, and typing commands')
    if any(arg.endswith('-stdin') or arg == '--stdin' for arg in arguments):
        raise ValueError('Use --input-file or a stdin option, not both')
    if path.stat().st_size > 4_000_000:
        raise ValueError('Input file exceeds the 4 MB safety limit')
    text = path.read_bytes().decode('utf-8-sig')
    if len(text) > 1_000_000:
        raise ValueError('Input exceeds the 1,000,000 character safety limit')
    return [*arguments, flag], text.encode('utf-8')


def _cdp_command(arguments: list[str]) -> str:
    # All value-taking global options in the retained CDP parser.
    takes_value = {'--endpoint', '--user-data-dir', '--chrome-path', '--debug-address', '--launch-timeout'}
    index = 0
    while index < len(arguments):
        item = arguments[index]
        if item in takes_value:
            index += 2
        elif item.startswith('-'):
            index += 1
        else:
            return item
    return ''



def mem_module():
    spec = importlib.util.spec_from_file_location('_webmind_mem_runtime', COMPONENTS['mem'])
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def initialization_status() -> dict[str, Any]:
    module = mem_module()
    return module.initialization_status()


def is_initialization_command(component: str, arguments: list[str]) -> bool:
    return component == 'mem' and any(item in INIT_MEM_COMMANDS for item in arguments)

def doctor() -> int:
    native = platform.system() == 'Darwin'
    dependencies = {label: importlib.util.find_spec(module) is not None for label, module in (
        ('Pillow', 'PIL'), ('mss', 'mss'), ('PyAutoGUI', 'pyautogui'))}
    dependencies['Quartz'] = importlib.util.find_spec('Quartz') is not None
    data = data_dir()
    scripts = {name: path.is_file() for name, path in COMPONENTS.items()}
    permissions: dict[str, Any] = {}
    if native:
        try:
            permissions = macos_permissions()
        except Exception as exc:
            permissions = {'check_error': str(exc)}
    chrome = None
    chrome_error = None
    try:
        spec = importlib.util.spec_from_file_location('_webmind_doctor_cdp', COMPONENTS['cdp'])
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        chrome = module.find_chrome_executable()
    except Exception as exc:
        chrome_error = str(exc)
    runtime_ok = native and sys.version_info >= MINIMUM_PYTHON and all(scripts.values()) and all(dependencies.values())
    gui_ready = None
    if platform.system() == 'Darwin' and permissions:
        gui_ready = all(permissions.get(p) is True for p in ('screen_recording', 'accessibility'))
    init = initialization_status()
    result = {'ok': runtime_ok, 'runtime_ready': runtime_ok, 'gui_permissions_ready': gui_ready,
              'browser_available': bool(chrome), 'native_host': native,
              'python': platform.python_version(), 'platform': platform.platform(), 'root': str(ROOT),
              'data_dir': str(data), 'initialization': init,
              'venv_python': str(venv_python(data)), 'dependencies': dependencies, 'components': scripts,
              'chrome': chrome, 'chrome_error': chrome_error, 'codex_on_path': bool(shutil.which('codex')),
              'host_permissions': permissions,
              'notes': ['No screenshot, mouse action or browser launch is performed by doctor.',
                        'runtime_ready does not prove that a real GUI task works. Check gui_permissions_ready and the smoke-test checklist.',
                        'Codex sandbox permissions and OS GUI permissions are separate. Request specific approvals; never disable safeguards automatically.']}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if runtime_ok else 1


def main(argv: list[str] | None = None) -> int:
    configure_utf8_stdio()
    parser = argparse.ArgumentParser(description='webmind-codex on macOS. Text commands accept --input-file FILE.')
    parser.add_argument('component', choices=[*COMPONENTS, 'doctor'])
    parser.add_argument('arguments', nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)
    try:
        if args.component == 'doctor':
            if any(arg not in {'--json'} for arg in args.arguments):
                parser.error('doctor only accepts --json')
            return doctor()
        if sys.version_info < MINIMUM_PYTHON:
            raise RuntimeError('Python 3.10 or newer is required')
        # Memory and waits are portable and need no active GUI. CLI help is also safe.
        help_only = '--help' in args.arguments or '-h' in args.arguments
        if not help_only and not is_initialization_command(args.component, args.arguments):
            init = initialization_status()
            if not init.get('initialized'):
                raise RuntimeError(
                    'webmind initialization is required before normal use. Recommend the usage tutorial and safety notice, '
                    'obtain the user choice to continue, then use mem scan/name-info/init to select an external xxx-yyy-mem folder. '
                    'When creating a new Mem, explicitly tell the user that both xxx and yyy must be unique on this Mac.'
                )
        if args.component not in {'mem', 'wait'} and not help_only:
            require_native_host()
        if args.component in {'screenshot', 'mouse', 'typing'} and not help_only:
            command = args.arguments[0] if args.arguments else ''
            if command not in {'self-check', 'list-keys'}:
                gui_preflight(args.component)
        arguments, content = prepare_input(args.component, args.arguments)
        env = os.environ.copy()
        env.update({'WEBMIND_CODEX_DATA_DIR': str(data_dir()), 'WEBMIND_MEM_LOCATION_FILE': str(MEM_LOCATION_FILE), 'PYTHONUTF8': '1',
                    'PYTHONIOENCODING': 'utf-8', 'PYTHONDONTWRITEBYTECODE': '1'})
        command = [sys.executable, '-B', str(COMPONENTS[args.component]), *arguments]
        options: dict[str, Any] = {'check': False, 'env': env}
        if content is not None:
            options['input'] = content
        return subprocess.run(command, **options).returncode
    except (OSError, RuntimeError, ValueError) as exc:
        if '--json' in args.arguments:
            print(json.dumps({'ok': False, 'error': str(exc)}, ensure_ascii=False))
        else:
            print(f'error: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
