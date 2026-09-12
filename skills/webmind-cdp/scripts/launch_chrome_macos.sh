#!/bin/bash
# Internal macOS launch helper for webmind-claudecode.
# Uses the macOS LaunchServices open -na strategy. The Python CDP client resolves
# the app/profile/port, checks readiness without a proxy, and verifies ownership.
set -euo pipefail

if [[ "${1:-}" == "--help" ]]; then
  printf '%s\n' 'Usage: launch_chrome_macos.sh /absolute/path/Browser.app CHROME_ARGUMENTS...'
  printf '%s\n' 'Internal helper: use the project launcher cdp launch for readiness/profile checks.'
  exit 0
fi
if [[ "$#" -lt 2 ]]; then
  printf '%s\n' 'Expected an absolute .app bundle path and validated Chrome arguments.' >&2
  exit 2
fi
chrome_app="$1"
shift
case "$chrome_app" in
  /*.[aA][pP][pP]) ;;
  *) printf '%s\n' 'Chrome application must be an absolute .app bundle path.' >&2; exit 2 ;;
esac
if [[ ! -d "$chrome_app/Contents/MacOS" ]]; then
  printf '%s\n' 'Chrome application bundle was not found.' >&2
  exit 1
fi

# LaunchServices owns Chrome's lifetime. Do not invoke the browser binary,
# background it with &, or wait for the browser process with open -W.
exec /usr/bin/open -na "$chrome_app" --args "$@"
