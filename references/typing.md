# Desktop keyboard input

Use `scripts/webmind_typing.py` for keyboard input in the visible, focused application. It requires the optional `requirements-desktop.txt` packages; `--help` works without them.

Before every new input action, verify the intended application, focused field, caret position, and an English / ABC / US-compatible keyboard layout. A screenshot can help confirm focus, but this script cannot inspect or change the input method and cannot prove where an application will route a shortcut. Cleanup releases should run promptly even if the original focus has changed.

**Literal typing supports printable ASCII plus tab, newline, and carriage return. It does not type Chinese, emoji, or other IME-driven text.** For Unicode text in webpages, use Core `fill` or `insert-text` with an explicit target selector. Native applications need a suitable Unicode-aware input method; this script does not manage the clipboard or IME.

## Commands

```bash
python scripts/webmind_typing.py self-check --json
python scripts/webmind_typing.py list-keys --json
python scripts/webmind_typing.py type --text "hello world" --interval 0.02 --json
python scripts/webmind_typing.py press --key enter --json
python scripts/webmind_typing.py press --key tab --presses 3 --interval 0.1 --json
python scripts/webmind_typing.py hotkey --keys ctrl shift p --json
python scripts/webmind_typing.py shortcut --keys command c --json
python scripts/webmind_typing.py down --key shift --json
python scripts/webmind_typing.py up --key shift --json
```

Select shortcuts appropriate to the active application and operating system: macOS commonly uses `command`, Windows/Linux commonly use `ctrl`. `shortcut` is an alias for `hotkey`. Key aliases include `cmd` → `command`, `control` → `ctrl`, `option` → `alt`, `return` → `enter`, and `esc` → `escape`; the normalized key must be supported by the backend.

Actions accept `--delay` before input. `type` and `press` accept `--interval` between characters or repeated presses; `hotkey` uses it between key-down operations. All times must be finite and nonnegative, and `--presses` must be positive. Text, keys, and numeric parameters are validated before sending input. If literal text contains shell metacharacters, pass it as a properly quoted argument or through the host's argument-array API.

## Holding keys and failure handling

`hotkey` presses its keys in order and releases them in reverse order in `finally`, including when a later key operation fails. Normal input keeps PyAutoGUI's failsafe enabled. Cleanup and explicit `up` temporarily bypass it only for key releases and restore the prior setting, so reaching a failsafe corner does not prevent release. Cleanup attempts to release every key even if one release fails.

The separate `down` command intentionally leaves a key held after that process exits. The host must pair it with `up` in a `finally` cleanup path around the whole multi-command operation. Prefer `hotkey` when a shortcut expresses the task. Process termination or an operating-system input failure can prevent release; this is not a system-wide key-state manager.

With `--json`, results and runtime errors go to stdout; errors have `ok: false` and a nonzero exit code. Parser errors go to stderr with exit code 2. Successful actions report normalized keys, timing, warnings, and `outcome_verified: false`. They do not verify that the receiving application accepted the text or shortcut; inspect the resulting UI. `self-check` and `list-keys` do not send keyboard events.

Return to the [suite README](../README.md) or continue with [Wait](wait.md).
