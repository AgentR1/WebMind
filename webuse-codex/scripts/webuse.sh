#!/usr/bin/env bash
set -euo pipefail
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
python_bin="${WEBUSE_PYTHON:-python3}"
if ! command -v "$python_bin" >/dev/null 2>&1; then
  echo "Python 3.10+ is required. Install Python or set WEBUSE_PYTHON to its executable." >&2
  exit 1
fi
exec "$python_bin" -B "$root/scripts/bootstrap.py" "$@"
