#!/usr/bin/env python3
"""Resolve the installed runtime without assuming a Codex-specific env variable."""
from __future__ import annotations
import os
from pathlib import Path
import subprocess
import sys
from runtime import ROOT, configure_utf8_stdio, data_dir, venv_python


def main() -> int:
    configure_utf8_stdio()
    try:
        data = data_dir()
        interpreter = venv_python(data)
        executable = str(interpreter) if interpreter.is_file() else sys.executable
        env = os.environ.copy()
        env.update({'WEBUSE_CODEX_DATA_DIR': str(data), 'PYTHONUTF8': '1', 'PYTHONIOENCODING': 'utf-8', 'PYTHONDONTWRITEBYTECODE': '1'})
        result = subprocess.run([executable, '-B', str(ROOT / 'scripts' / 'webuse.py'), *sys.argv[1:]], env=env, check=False)
        return result.returncode
    except (OSError, ValueError) as exc:
        print(f'WebUse runtime error: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
