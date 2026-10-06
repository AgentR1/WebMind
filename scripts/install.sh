#!/usr/bin/env bash
set -euo pipefail
if [ "$(uname -s)" != "Darwin" ]; then
  echo "This edition requires native macOS." >&2
  exit 1
fi
python_executable="${WEBMIND_PYTHON:-python3}"
if ! command -v "$python_executable" >/dev/null 2>&1; then
  echo "Python 3.10 or newer was not found." >&2
  exit 1
fi
plugin_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
exec "$python_executable" -B "$plugin_root/scripts/install.py" "$@"
