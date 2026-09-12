#!/usr/bin/env bash
set -euo pipefail
if [ "$(uname -s)" != "Darwin" ]; then
  echo "This edition requires native macOS." >&2
  exit 1
fi

if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3.10 or newer was not found." >&2
  exit 1
fi

python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else "Python 3.10 or newer is required.")'

plugin_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
data_root="${WEBMIND_DATA_DIR:-${HOME}/Library/Application Support/WebMind}"
venv_root="${data_root}/.venv"

mkdir -p "${data_root}"
python3 -m venv "${venv_root}"
"${venv_root}/bin/python" -m pip install --upgrade pip
"${venv_root}/bin/python" -m pip install -r "${plugin_root}/requirements.txt"
"${venv_root}/bin/python" "${plugin_root}/scripts/webmind.py" doctor
