---
name: webuse-screenshot
description: claude code skill for reading the current graphical desktop resolution before every screen task, then taking a full-screen screenshot, left-half screenshot, right-half screenshot, or custom rectangular screenshot from x1,y1 to x2,y2. use when a task needs screen size detection, browser or desktop visual inspection, ui debugging, web automation evidence, or saving screenshots of the current target screen.
---

# webuse-screenshot

Use this skill when Claude Code needs to inspect the visible desktop by reading the screen resolution and optionally saving a screenshot.

## Cross-platform launcher

Commands below use `webuse` as shorthand. Translate `webuse screenshot ...`
to the current OS launcher:

```powershell
& "$env:CLAUDE_PLUGIN_ROOT\scripts\webuse.ps1" screenshot <command> [options]
```

```bash
bash "$CLAUDE_PLUGIN_ROOT/scripts/webuse.sh" screenshot <command> [options]
```

Do not depend on the current working directory. If dependencies are missing,
run the plugin's `scripts/install.ps1` or `scripts/install.sh` first.

## Mandatory rule

Before every task, always read the current screen resolution first. Do not guess screen size or reuse an old resolution. For screenshot tasks, use the same command's JSON output because every screenshot command reads the current resolution before capturing.

## Program file

Use the single bundled Python program:

```bash
webuse screenshot <command> [options]
```

Install dependencies when needed:

Install all plugin dependencies once with the platform-specific installer in
the plugin's root `scripts` directory.

Run a dependency check without taking a screenshot:

```bash
webuse screenshot self-check --json
```

## Commands

### 1. Read resolution only

Use this at the start of any screen-related workflow:

```bash
webuse screenshot resolution --json
```

Output includes `resolution`, `width`, `height`, `left`, `top`, `right`, `bottom`, backend, and monitor metadata when available.

### 2. Full-screen screenshot

```bash
webuse screenshot full --output screenshot_full.png --json
```

Captures the full virtual desktop, including the visible mouse pointer by
default, and returns the resolution first in JSON. Add `--no-cursor` when the
pointer should be omitted.

### 3. Half-screen screenshot

Left half:

```bash
webuse screenshot half --side left --output screenshot_left.png --json
```

Right half:

```bash
webuse screenshot half --side right --output screenshot_right.png --json
```

The half region is computed from the current virtual desktop resolution read at runtime.

### 4. Custom region screenshot

Capture from `(x1, y1)` to `(x2, y2)`:

```bash
webuse screenshot region --x1 100 --y1 100 --x2 900 --y2 700 --output screenshot_region.png --json
```

Coordinates are absolute positions on the current virtual desktop. The program validates that `x2 > x1`, `y2 > y1`, and the region stays inside the current desktop bounds.

## Choosing a screenshot mode

- Use `resolution` when only screen size is needed.
- Use `full` when the whole desktop/browser state matters.
- Use `half --side left` or `half --side right` when the relevant UI is known to occupy one side of the screen.
- Use `region` when the target location is known and a smaller crop is enough.

## Output contract

For all screenshot commands, JSON output includes:

- `ok`: true or false
- `task`: `resolution`, `full`, `half`, or `region`
- `resolution`: current desktop resolution string
- `desktop`: full virtual desktop bounds
- `region`: captured rectangle bounds and size
- `output`: absolute PNG path for screenshot commands
- `backend`: capture backend used
- `cursor`: whether cursor capture was requested and successfully included
- `monitors`: per-monitor metadata when available

Windows and macOS use a cursor-shaped marker sampled immediately before capture
from the live system pointer coordinates. Inspect `cursor.included`, `cursor.source`, and
`warnings`; a cropped screenshot correctly omits the pointer when it lies outside
the captured region.

## Environment notes

- A real graphical desktop session must be active. Headless CI, SSH-only sessions, and containers without a display normally cannot capture the user's screen.
- macOS may require Screen Recording permission for Terminal, Claude Code, or the app hosting the process.
- Windows and Linux usually require the command to run in the same user session that owns the visible desktop.
- Multi-monitor setups use the full virtual desktop. Report non-zero `left` and `top` values when the virtual desktop origin is not `(0, 0)`.

## Failure handling

If a command fails, report the script's error message and suggest the smallest next fix: install dependencies, enable screen-recording permissions, or run from an active graphical desktop session.
