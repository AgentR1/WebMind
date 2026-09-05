# Desktop mouse input

Use `scripts/webmind_mouse.py` for visible desktop tasks requiring pointer input. Install `requirements-desktop.txt` first. For webpage elements, prefer Core selectors and its interaction checks when available.

Before a click, hold, or scroll, inspect a fresh [screenshot](screenshot.md), read `position`, and identify the target. If a window, display, scale, or scroll position changed, observe again. The coordinates below are examples, not coordinates to execute without observation.

```bash
python scripts/webmind_mouse.py self-check --json
python scripts/webmind_mouse.py position --json
python scripts/webmind_mouse.py move-to --x 500 --y 300 --duration 0.1 --json
python scripts/webmind_mouse.py slide --dx 120 --dy 0 --duration 0.2 --json
python scripts/webmind_mouse.py slide --direction down --distance 80 --duration 0.2 --json
```

Coordinates use **PyAutoGUI's primary-screen coordinate system**, bounded by `0 <= x < screen.width` and `0 <= y < screen.height`. They are not guaranteed to match screenshot pixels or the virtual desktop. Secondary displays and mixed DPI need an explicitly verified mapping or another suitable input tool. `slide` accepts either `--dx` / `--dy` or the pair `--direction` / `--distance`, never both modes.

## Click, scroll, and hold

```bash
python scripts/webmind_mouse.py left-click --json
python scripts/webmind_mouse.py right-click --json
python scripts/webmind_mouse.py scroll --direction down --amount 3 --json
python scripts/webmind_mouse.py scroll --direction up --amount 3 --json
python scripts/webmind_mouse.py left-hold --seconds 1.5 --json
python scripts/webmind_mouse.py left-down --json
python scripts/webmind_mouse.py left-up --json
```

These commands accept optional `--x` and `--y` together to move before acting, plus `--duration`. Only use that convenience after verifying the coordinate mapping and target. Without them, the command acts at the current pointer position. Scroll amounts and directional distances must be positive integers. Durations and hold times must be finite, nonnegative numbers; invalid arguments are rejected before any movement or input.

Use small scroll amounts and recheck the resulting view. A long drag can be expressed as `left-down`, `slide`, and `left-up`. **The host must put the matching `left-up` in a `finally` cleanup path** so a failed intermediate command does not leave the button held. The separate `left-down` command intentionally leaves the button pressed across CLI invocations. Prefer `left-hold` for a timed hold; it attempts release in its own `finally` block.

PyAutoGUI's failsafe remains enabled during normal input. Timed-hold cleanup and explicit `left-up` temporarily bypass it only to release the left button, then restore the original setting. This allows release even after the pointer reaches a failsafe corner. Optional movement before `left-up` still obeys the failsafe, with release attempted in `finally`. A killed process or an operating-system input failure can still prevent cleanup.

## Results

`--json` returns `ok`, `action`, `screen`, `position_before`, `position_after`, `coordinate_space`, and `outcome_verified`. Additional fields describe the target, movement, scroll, or hold. Runtime errors return JSON to stdout with `ok: false` and a nonzero exit code; invalid command syntax goes to stderr with exit code 2.

`ok: true` means the requested desktop command ran. `outcome_verified: false` makes clear that WebMind has not proved the application accepted the click or reached the intended state. Observe the result before continuing. `self-check` and `position` read screen and pointer state without moving or clicking.

Return to the [suite README](../README.md) or continue with [Typing](typing.md).
