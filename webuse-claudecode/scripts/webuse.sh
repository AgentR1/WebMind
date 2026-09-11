#!/usr/bin/env bash
set -euo pipefail

plugin_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
data_root="${WEBUSE_DATA_DIR:-${HOME}/Library/Application Support/WebUse}"
venv_python="${data_root}/.venv/bin/python"

if [[ -x "${venv_python}" ]]; then
  exec "${venv_python}" "${plugin_root}/scripts/webuse.py" "$@"
fi

if command -v python3 >/dev/null 2>&1; then
  exec python3 "${plugin_root}/scripts/webuse.py" "$@"
fi

echo "Python 3.10 or newer was not found. Install Python, then run scripts/install.sh." >&2
exit 1
