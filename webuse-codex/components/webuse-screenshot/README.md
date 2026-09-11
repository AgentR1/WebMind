# webuse-screenshot

Codex Skill for reading the current graphical desktop resolution before every screen task, then capturing full-screen, half-screen, or custom rectangular screenshots.

Main file: `scripts/webuse_screenshot.py`

## Install runtime dependencies

Use the project-level platform installer in `scripts/` to install dependencies.

## Commands

```bash
webuse screenshot self-check --json
webuse screenshot resolution --json
webuse screenshot full --output screenshot_full.png --json
webuse screenshot half --side left --output screenshot_left.png --json
webuse screenshot half --side right --output screenshot_right.png --json
webuse screenshot region --x1 100 --y1 100 --x2 900 --y2 700 --output screenshot_region.png --json
```

Every screenshot command reads the current resolution first and includes the
visible mouse pointer by default. Linux uses mss native cursor capture when the
backend supports it; other platforms draw a cursor marker at the live system
pointer position after capture. Add `--no-cursor` when an unannotated screenshot
is required. JSON output contains the desktop bounds, captured region, backend,
cursor status, monitor metadata, and output PNG path.

## Notes

This version uses `mss.MSS()` when available, with a fallback to the older
`mss.mss()` constructor for compatibility with older `mss` releases. On Windows,
where mss does not natively composite the cursor, the script reads the pointer
through the Win32 API (with a pyautogui fallback) and draws a cursor-shaped marker
with its tip at that exact desktop coordinate. The JSON `cursor` field reports
the source, position, and whether the marker was included.
