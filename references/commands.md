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
| `--url-contains TEXT` | Select a unique page whose URL contains the text. |
| `--title-contains TEXT` | Select a unique page whose title contains the text. |
| `--cdp-timeout SECONDS` | CDP request timeout; default 10. |
| `--accept-js-dialogs` | Accept JavaScript dialogs observed after the command; use when the requested action includes accepting them. |
| `--dialog-drain SECONDS` | Time to look for those dialogs; default 0.5. |

Prefer a single target selector and an explicit ID from a `type: "page"` entry. Selection requires a unique matching page: without a filter, only one eligible page may be available; ambiguous matches and non-page targets are rejected. An ID is only useful while that target exists; re-list tabs if it closes or is replaced.

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
python3 scripts/webmind.py read-page --target-id TAB_ID --wait-selector "h1" --max-chars 20000 --max-links 100 --timeout 10 --json
```

### Navigation results

`navigate` reports `status`, `result`, `load_event_seen`, and `outcome_verified: false`. Check the status rather than treating every accepted CDP request as a loaded page:

| Status | Meaning | `ok` |
| --- | --- | --- |
| `loaded` | A load lifecycle event matches this navigation's frame and loader. | `true` |
| `same-document` | No new loader was created and the same-document destination was confirmed. | `true` |
| `dispatched` | Navigation was sent without waiting for loading. | `true` |
| `failed` | CDP reported a navigation error. | `false` |
| `download` | The navigation triggered a download rather than a page load. | `false` |
| `timeout` | The requested navigation confirmation did not arrive in time. | `false` |

Failures include a top-level `error`; `ok: false` exits with code 1. Even `loaded` does not establish that the page contains the requested content or that dynamic rendering is complete. Inspect the destination and wait for task-specific content.

### Read page content

`read-page` is the default command for webpage reading. It extracts a snapshot from the current document, choosing a likely main-content region and falling back to the body. It filters common navigation, sidebar, footer, form-control, script, and hidden content. These are heuristics, so inspect the result and override the region when needed.

| Option | Meaning |
| --- | --- |
| `--selector CSS` | Override extraction with exactly one matching region; hidden or ambiguous matches are rejected. |
| `--max-chars N` | Positive text-character limit; default 20,000. |
| `--max-links N` | Nonnegative link limit; default 100. Set to 0 to omit links. |
| `--wait-selector CSS` | Wait for a selector to exist before extraction; does not require visibility. |
| `--timeout SECONDS` | Positive wait timeout; default 10. |

For a region observed in the DOM:

```bash
python3 scripts/webmind.py read-page --target-id TAB_ID --selector "article" --max-chars 12000 --max-links 30 --json
```

Successful responses include `ok`, `action`, `target`, and `page`:

| Field inside `page` | Content |
| --- | --- |
| `title`, `url`, `lang` | Document identity and language; title may fall back to an H1. |
| `text` | Extracted text, bounded by `--max-chars`. |
| `headings` | Heading objects with `level` and `text`, up to 100 items. |
| `links` | Objects with `text` and `url`; HTTP(S) links from the extracted region, deduplicated by URL. |
| `extraction` | `method` and `selector` identifying the extraction choice. |
| `truncated` | Independent `text`, `links`, and `headings` flags. |

Heading text and link labels are each limited to 300 characters. A `truncated` flag means the output omits content; adjust limits or read a narrower region before claiming complete coverage. Waiting past `--timeout` returns `ok: false`, `status: "timeout"`, and an error, with exit code 1.

This command does not perform OCR, traverse iframe documents or Shadow DOM, bypass login, or make unavailable content accessible. It reads what the current browser session exposes. See [reading workflows](../examples/reading-workflows.md) for authenticated and dynamic pages.

### Custom DOM queries and readiness

```bash
python3 scripts/webmind.py wait-for-selector --target-id TAB_ID --selector "main" --visible --timeout 10 --interval 0.25 --json
python3 scripts/webmind.py eval --target-id TAB_ID --expression "({url: location.href, ready: document.readyState, articleCount: document.querySelectorAll('article').length})" --json
```

Use `eval` when structured page data or a specific field needs a custom query. It runs JavaScript in the selected page and returns its value; expressions can mutate state, so stay within the requested task. `wait-for-selector --visible` checks for a nonzero layout box, not whether an overlay covers the element. A selector wait timeout is a failure with exit code 1.

## Interact and verify

```bash
python3 scripts/webmind.py fill --target-id TAB_ID --selector "input[name=q]" --text "search terms" --json
python3 scripts/webmind.py eval --target-id TAB_ID --expression "document.querySelector('input[name=q]').value" --json
python3 scripts/webmind.py click --target-id TAB_ID --selector "button[type=submit]" --json
```

`fill` sets an input-like value with the native setter and dispatches `input`/`change`, or replaces the text of a contenteditable element. It rejects disabled, read-only, or inert elements. `click` scrolls the selected element into view and checks that its center is not covered before sending mouse events there; hidden or disabled targets are rejected. These element commands use the first CSS match, so choose a specific selector after inspection. This differs from tab selection, which requires a unique page target.

Successful input commands report `status: "dispatched"` and `outcome_verified: false`. A fill's `immediate_value_verified: true`, also present inside `result`, confirms that its DOM value matched immediately after synchronous input/change handlers; it does not verify a later framework update or server acceptance. Verify the resulting field value, validation message, URL, or relevant DOM state.

```bash
python3 scripts/webmind.py insert-text --target-id TAB_ID --selector "textarea" --text "hello" --json
python3 scripts/webmind.py press --target-id TAB_ID --key Enter --json
```

`insert-text` focuses the selected element and calls CDP `Input.insertText`; it does not clear existing text first. It rejects disabled, read-only, inert, or non-text targets and confirms focus before dispatch, reporting `focus_verified: true` on success. This verifies focus, not the website's response to the text. `press` sends one key to the focused page element. Supported examples include `Enter`, `Tab`, `Escape`, `ArrowDown`, and a single character. Ensure focus is correct and verify the result.

## Screenshots and JavaScript dialogs

```bash
python3 scripts/webmind.py screenshot --target-id TAB_ID --output page.png --json
python3 scripts/webmind.py handle-js-dialog --target-id TAB_ID --dismiss --timeout 3 --json
python3 scripts/webmind.py handle-js-dialog --target-id TAB_ID --accept --prompt-text "requested answer" --timeout 3 --json
```

`screenshot` writes a PNG of the page viewport. It does not capture the full document or desktop. `handle-js-dialog` handles JavaScript alert/confirm/prompt dialogs; choose exactly one of `--accept` and `--dismiss`. `--prompt-text` supplies a prompt response when accepting. Native dialogs and browser UI require the host's GUI tools.

## Inspect failures

Use the JSON `ok`, `status`, `error`, and command-specific fields, plus the process exit code. An `ok: false` result exits with code 1; an invalid CLI argument is rejected by the argument parser. Command success is not task completion: read the resulting page when an outcome matters.

For endpoint failures, run `self-check` with the same endpoint, confirm the browser executable, and check that `/json/version` and `/json/list` are available. For selection errors, re-list tabs or inspect the DOM and choose a unique target. For timeouts, check the current page before retrying. Avoid repeating an action with external side effects until you have checked whether it already succeeded. See [failure recovery examples](../examples/reading-workflows.md#recover-from-failures).
