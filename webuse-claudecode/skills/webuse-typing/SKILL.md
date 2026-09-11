---
name: webuse-typing
description: Claude Code skill for real keyboard-like input automation. Use when Claude Code needs to type standard English keyboard characters, spaces, tabs, enters, press individual keys, hold and release modifier keys such as ctrl or shift, or execute keyboard shortcuts/hotkeys such as ctrl+c, ctrl+v, ctrl+s, command+tab, or shift+enter. Before every typing or key action, Claude Code must ensure the cursor/insertion point is in the correct target position and the active input method or keyboard layout is English; do not use this skill to type Chinese text through an IME.
---

# webuse-typing

Use this skill when Claude Code needs to simulate real keyboard input in the active desktop session.

## Cross-platform launcher

Commands below use `webuse` as shorthand. Translate `webuse typing ...` to:

```powershell
& "$env:CLAUDE_PLUGIN_ROOT\scripts\webuse.ps1" typing <command> [options]
```

```bash
bash "$CLAUDE_PLUGIN_ROOT/scripts/webuse.sh" typing <command> [options]
```

Do not depend on the current working directory. If dependencies are missing,
run the plugin's platform-specific installer first.

## Critical rules

1. Before every keyboard action, ensure the cursor / insertion point is in the correct target position.
2. Before every keyboard action, ensure the active input method / keyboard layout is English.
3. Do not use this skill to type Chinese text through a Chinese IME.
4. If the requested content contains Chinese or other non-standard keyboard characters, do not type it with this tool. Ask the user for another method or use a clipboard/paste workflow outside this skill only when explicitly allowed.
5. The target application and text field must already be focused before typing. If focus or cursor placement is uncertain, use screenshot and mouse-control skills first to focus the correct target and verify the insertion point.
6. Prefer the smallest safe action: use `type` for literal English text, `press` for one key, `hotkey` for shortcuts, and `down`/`up` only when a long hold is required.
7. Keep `pyautogui` failsafe enabled. Moving the pointer to the upper-left corner should interrupt automation.
8. Literal `type` accepts printable ASCII only. Send Tab, Enter, and other control keys with `press`; do not embed them in `--text` or stdin.
9. Do not put secrets or other critical private values in `--text`, stdin, shell history, or logs. Pause for direct user entry instead.

## Program

Run the bundled program:

```bash
webuse typing --help
```

The program uses `pyautogui`. Install the plugin dependencies with the
platform-specific installer in the plugin's root `scripts` directory.

## Required preflight before any action

Before running `type`, `press`, `hotkey`, `down`, or `up`:

1. Ensure the intended app/window/input field is focused.
2. Ensure the text cursor / insertion point is exactly where the next keystroke should land.
3. If cursor placement is uncertain, take a screenshot and use mouse-control or navigation keys to place the cursor correctly before typing.
4. Ensure the system input method is English / ABC / US keyboard / equivalent.
5. If the input method is uncertain, switch it to English before running the command.
6. If the text includes Chinese characters, stop and do not type it through this skill.

## Commands

### Type literal standard-keyboard text

```bash
webuse typing type --text "hello world" --interval 0.02
```

Use this for standard English keyboard characters, including spaces and symbols such as `!@#$%^&*()_+-=[]{};':",./<>?`.

For non-sensitive text that should not appear in process arguments, pipe a
single-line printable-ASCII value and use `--stdin`:

```powershell
"hello world" | & "$env:CLAUDE_PLUGIN_ROOT\scripts\webuse.ps1" typing type --stdin --interval 0.02
```

```bash
printf %s "hello world" | bash "$CLAUDE_PLUGIN_ROOT/scripts/webuse.sh" typing type --stdin --interval 0.02
```

### Press a single key

```bash
webuse typing press --key enter
webuse typing press --key space
webuse typing press --key tab --presses 3
```

### Run a shortcut / hotkey

```bash
webuse typing hotkey --keys ctrl s
webuse typing hotkey --keys ctrl shift p
webuse typing hotkey --keys command tab
webuse typing hotkey --keys primary s
```

Use `command` on macOS where the user expects the Command key. Use `ctrl` for Windows/Linux shortcuts.
Use the portable alias `primary` for Command on macOS and Ctrl on Windows.

### Hold and release a key

```bash
webuse typing down --key shift
webuse typing press --key a
webuse typing up --key shift
```

Use `down` and `up` for long holds or drag-like keyboard interactions. Always release held keys after use.

### List supported key names

```bash
webuse typing list-keys
```

### Environment check

```bash
webuse typing self-check --json
```

This checks Python/package availability only. It cannot guarantee GUI permissions, focused app state, or current input method.

## Output behavior

Use `--json` for machine-readable results:

```bash
webuse typing hotkey --keys ctrl s --json
```

The command reports the requested action, normalized keys, timing, and warnings. It cannot verify that the receiving application accepted the keystrokes.

## Safety notes for Claude Code

- Never send destructive shortcuts, such as deleting files or closing unsaved work, unless the user explicitly requested that exact action.
- For multi-step UI automation, type small chunks and verify the cursor position and UI state between steps when the consequence matters.
- If a modifier is pressed with `down`, always pair it with `up`, even after an error.
