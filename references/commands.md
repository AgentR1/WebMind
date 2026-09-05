# Command reference

Run examples from the skill directory with Python 3.10+. On Windows, `py -3` may replace `python3`. Replace `TAB_ID` with a page ID returned by `tabs`, and selectors with ones observed in the current DOM.

```text
python3 scripts/webmind.py [global options] COMMAND [command options] --json
```

## Global options

| Option | Behavior |
| --- | --- |
| `--endpoint URL` | CDP endpoint; default `http://127.0.0.1:9222`. |
| `--chrome-path PATH` | Browser executable; otherwise `WEBMIND_CHROME`, then discovery. |
| `--user-data-dir PATH` | Persistent profile; otherwise `WEBMIND_PROFILE`, then the skill's `chrome-profile/`. |
| `--launch-timeout SECONDS` | Time to wait for the endpoint after launch; default 10. |
| `--no-auto-launch` | Disable implicit browser launch. |
| `--debug-address ADDRESS` | Debugging bind address; default `127.0.0.1`. Keep it local. |

Place these before the command. For example:

```bash
python3 scripts/webmind.py --endpoint http://127.0.0.1:9334 tabs --json
```

## Target options

All commands except `self-check`, `tabs`, and `launch` accept:

| Option | Behavior |
| --- | --- |
| `--target-id ID` | Select the exact observed target; preferred. |
| `--url-contains TEXT` | Select the first page whose URL contains the text. |
| `--title-contains TEXT` | Select the first page whose title contains the text. |
| `--cdp-timeout SECONDS` | CDP request timeout; default 10. |
| `--accept-js-dialogs` | Accept JavaScript dialogs observed after the command; use when the requested action includes accepting them. |
| `--dialog-drain SECONDS` | Time to look for those dialogs; default 0.5. |

Prefer a single target selector and an explicit ID from a `type: "page"` entry. Automatic selection prefers page targets but can fall back to another debuggable target when no page is available. An ID is only useful while that target exists; re-list tabs if it closes or is replaced.

## Connection commands

```bash
python3 scripts/webmind.py self-check --json
python3 scripts/webmind.py launch --json
python3 scripts/webmind.py tabs --json
```

`self-check` probes the endpoint without launching. `launch` starts the dedicated browser or reuses a responding endpoint. Optional launch flags are `--url URL`, `--new-window`, and `--port PORT`; these affect a new browser launch. `--port` also selects the endpoint port for the launch command. Prefer the global `--endpoint` consistently across commands. `launch --url` does not navigate a reused browser.

`tabs` lists target IDs, types, titles, URLs, and whether WebSocket access is available. It can launch the local dedicated browser if needed.

## Read and navigate

```bash
python3 scripts/webmind.py navigate --target-id TAB_ID --url "https://example.com" --wait-load --timeout 15 --json
python3 scripts/webmind.py wait-for-selector --target-id TAB_ID --selector "main" --visible --timeout 10 --interval 0.25 --json
python3 scripts/webmind.py eval --target-id TAB_ID --expression "({title: document.title, url: location.href, text: document.body.innerText})" --json
```

`navigate` reports `load_event_seen` when `--wait-load` is used. Inspect that field and the actual page state; a successful command response alone does not establish completed loading. `wait-for-selector --visible` checks for a nonzero layout box, not whether an overlay covers the element. `eval` runs JavaScript in the selected page and returns its value; page scripts can also mutate state, so keep expressions within the requested task.

## Interact and verify

```bash
python3 scripts/webmind.py fill --target-id TAB_ID --selector "input[name=q]" --text "search terms" --json
python3 scripts/webmind.py eval --target-id TAB_ID --expression "document.querySelector('input[name=q]').value" --json
python3 scripts/webmind.py click --target-id TAB_ID --selector "button[type=submit]" --json
```

`fill` sets an input-like value and dispatches `input`/`change`, or replaces the text of a contenteditable element. `click` scrolls the first matching element into view and sends mouse events at its center. Neither command guarantees the website accepted the change. Verify the resulting field value, validation message, URL, or relevant DOM state.

```bash
python3 scripts/webmind.py insert-text --target-id TAB_ID --selector "textarea" --text "hello" --json
python3 scripts/webmind.py press --target-id TAB_ID --key Enter --json
```

`insert-text` focuses the selected element and calls CDP `Input.insertText`; it does not clear existing text first. `press` sends one key to the focused page element. Supported examples include `Enter`, `Tab`, `Escape`, `ArrowDown`, and a single character. Ensure focus is correct and verify the result.

## Screenshots and JavaScript dialogs

```bash
python3 scripts/webmind.py screenshot --target-id TAB_ID --output page.png --json
python3 scripts/webmind.py handle-js-dialog --target-id TAB_ID --dismiss --timeout 3 --json
python3 scripts/webmind.py handle-js-dialog --target-id TAB_ID --accept --prompt-text "requested answer" --timeout 3 --json
```

`screenshot` writes a PNG of the page viewport. It does not capture the full document or desktop. `handle-js-dialog` handles JavaScript alert/confirm/prompt dialogs; choose exactly one of `--accept` and `--dismiss`. `--prompt-text` supplies a prompt response when accepting. Native dialogs and browser UI require the host's GUI tools.

## Inspect failures

Use the JSON `ok` field and command-specific results, then read the page when an outcome matters. For endpoint failures, run `self-check`, confirm the browser executable, and check that `/json/version` and `/json/list` are available at the selected endpoint. Avoid retrying an action with external side effects until you have checked whether it already succeeded.
