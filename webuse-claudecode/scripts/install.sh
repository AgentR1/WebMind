#!/usr/bin/env bash
set -euo pipefail

plugin_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
data_root="${WEBUSE_DATA_DIR:-${HOME}/Library/Application Support/WebUse}"
venv_root="${data_root}/.venv"

mkdir -p "${data_root}"
python3 -m venv "${venv_root}"
"${venv_root}/bin/python" -m pip install --upgrade pip
"${venv_root}/bin/python" -m pip install -r "${plugin_root}/requirements.txt"
"${venv_root}/bin/python" "${plugin_root}/scripts/webuse.py" doctor
