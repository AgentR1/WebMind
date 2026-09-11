---
name: webuse-mouse-control
description: Control the local mouse pointer from Claude Code for GUI automation. Use when Claude Code needs to place the cursor at an exact x/y coordinate, slide or drag the cursor by a distance, perform a left-click, hold and release the left mouse button, perform a right-click, or scroll the mouse wheel up/down by a chosen amount. This skill is intended for direct desktop interaction after visual inspection or screenshot-based coordinate selection.
---

# webuse-mouse-control

Use this skill when Claude Code needs to control the local mouse pointer during desktop or browser automation.

## Cross-platform launcher

Commands below use `webuse` as shorthand. Translate `webuse mouse ...` to:

```powershell
& "$env:CLAUDE_PLUGIN_ROOT\scripts\webuse.ps1" mouse <command> [options]
```

```bash
bash "$CLAUDE_PLUGIN_ROOT/scripts/webuse.sh" mouse <command> [options]
```

Do not depend on the current working directory. If dependencies are missing,
run the plugin's platform-specific installer first.

## Program file

Run the bundled Python program:

```bash
webuse mouse --help
```

The program uses `pyautogui` and `mss`. Install the plugin dependencies with
the platform-specific installer in the plugin's root `scripts` directory.

## Safety and coordinate rules

- Always use screen coordinates in pixels.
- Coordinates are absolute virtual-desktop coordinates unless a command explicitly says otherwise; negative x/y values are valid when a monitor is left of or above the primary display.
- Before acting on coordinates derived from a screenshot, make sure the coordinate system matches the current display arrangement.
- Prefer short movements and explicit coordinates.
- Keep `pyautogui` failsafe enabled: moving the physical mouse to the top-left corner can interrupt automation.
- Do not use this skill for hidden, destructive, or unauthorized interaction. Use it only for the current user-visible desktop session.


## Required screenshot confirmation before clicking or scrolling

Claude Code MUST confirm the cursor position with a screenshot before every click-style action and before every mouse wheel scroll action. This rule applies to:

- `left-click`
- `right-click`
- `left-down`
- `left-up`
- `left-hold`
- `scroll`

Required workflow before any click-style or scroll action:

1. Determine the intended target coordinate.
2. Move the cursor to the intended coordinate when needed, for example:

```bash
webuse mouse move-to --x 500 --y 300 --duration 0.1 --json
```

3. Take a screenshot with the available screenshot skill/tool, preferably `webuse-screenshot`, to visually confirm that the cursor is positioned on the intended target.
4. Only after confirming the cursor is correctly positioned, run the click-style or scroll command.
5. If the screenshot shows the cursor is not correctly positioned, do not click or scroll. Recalculate the coordinate, move again, and take another screenshot first.

Never combine coordinate selection with clicking or scrolling blindly. Screenshot confirmation is mandatory immediately before clicking, pressing, holding, releasing the mouse button, or scrolling the mouse wheel.

## Commands

### 1. Check environment

```bash
webuse mouse self-check --json
```

Use this to confirm `pyautogui` is available and to read the current screen size and cursor position.

### 2. Get current position

```bash
webuse mouse position --json
```

Returns the current mouse position and virtual-desktop bounds (`left`, `top`, `width`, and `height`).

### 3. Move cursor to an exact coordinate

```bash
webuse mouse move-to --x 500 --y 300 --duration 0.1 --json
```

Use this when Claude Code has selected a target point such as `x=500, y=300`.

### 4. Slide cursor by an offset

Use direct x/y offsets:

```bash
webuse mouse slide --dx 120 --dy 0 --duration 0.2 --json
```

Or use direction plus distance:

```bash
webuse mouse slide --direction right --distance 120 --duration 0.2 --json
webuse mouse slide --direction left --distance 120 --duration 0.2 --json
webuse mouse slide --direction up --distance 80 --duration 0.2 --json
webuse mouse slide --direction down --distance 80 --duration 0.2 --json
```

Positive `dx` moves right, negative `dx` moves left. Positive `dy` moves down, negative `dy` moves up.


### 5. Scroll mouse wheel

Scroll up at the current cursor position:

```bash
webuse mouse scroll --direction up --amount 5 --json
```

Scroll down at the current cursor position:

```bash
webuse mouse scroll --direction down --amount 5 --json
```

Move to a coordinate first, then scroll:

```bash
webuse mouse scroll --x 500 --y 300 --direction down --amount 6 --json
```

Use small amounts first, such as `3` to `8`, then repeat after another screenshot if more scrolling is needed. Claude Code must screenshot-confirm the cursor position immediately before every scroll action.

### 6. Left-click once

```bash
webuse mouse left-click --json
```

To move first and then click:

```bash
webuse mouse left-click --x 500 --y 300 --json
```

### 7. Left-button press and release for long press or drag-style workflows

Press down:

```bash
webuse mouse left-down --json
```

Release:

```bash
webuse mouse left-up --json
```

Long press at current position:

```bash
webuse mouse left-hold --seconds 1.5 --json
```

Long press at a coordinate:

```bash
webuse mouse left-hold --x 500 --y 300 --seconds 1.5 --json
```

For drag-like motion, use `left-down`, then `slide`, then `left-up`:

```bash
webuse mouse left-down --x 500 --y 300 --json
webuse mouse slide --dx 200 --dy 0 --duration 0.4 --json
webuse mouse left-up --json
```

### 8. Right-click

```bash
webuse mouse right-click --json
```

To move first and then right-click:

```bash
webuse mouse right-click --x 500 --y 300 --json
```

## Output format

Use `--json` for machine-readable output. Successful commands return JSON like:

```json
{
  "ok": true,
  "action": "move-to",
  "screen": {"width": 1440, "height": 900},
  "position_before": {"x": 100, "y": 100},
  "position_after": {"x": 500, "y": 300}
}
```

If an action fails, the program exits non-zero and returns an error message, or a JSON object with `ok: false` when `--json` is used.
