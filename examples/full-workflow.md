# A task across the WebMind modules

This example shows how a host agent can combine experience, browser controls, and desktop tools for a requested web task. It is a workflow template, not a recorded site benchmark. Run commands from the skill directory. On Windows, use `py -3` instead of `python3`; for desktop commands, use the virtual-environment interpreter from the [installation guide](../README.md#optional-desktop-dependencies).

## Consult relevant experience

Read the [memory guide](../references/memory.md), then check the selected store and find experience relevant to the task:

```bash
python3 scripts/webmind_memory.py check --json
python3 scripts/webmind_memory.py read --scope global --json
python3 scripts/webmind_memory.py search --query "example.com" --limit 5 --json
```

The default store is `~/.local/share/webmind/Mem`; `WEBMIND_MEM` or `--mem-path` can override it. The read/check/search commands do not create missing experience. If the store does not exist, the task can proceed from current observations; initialize one only when persistent writes are authorized.

Read a relevant task record returned by the search, using its actual task and file names. Check its date, status, prerequisites, and evidence. An old selector or successful past action is only a hypothesis about the current page and never grants permission for a new external action.

## Use Core for the webpage

```bash
python3 scripts/webmind.py tabs --json
python3 scripts/webmind.py navigate --target-id TAB_ID --url "https://example.com" --wait-load --json
python3 scripts/webmind.py read-page --target-id TAB_ID --wait-selector "h1" --json
```

Replace `TAB_ID` with the intended `type: "page"` ID from `tabs`. Confirm the URL, navigation status, extracted region, and truncation flags before relying on the content. Use current DOM evidence to select fields or controls, and inspect the result after each meaningful action. See [reading workflows](reading-workflows.md) for dynamic pages, login sessions, and recovery.

## Use desktop tools when the task reaches native UI

A native file picker or browser permission bubble requires desktop observation. Read the [screenshot guide](../references/screenshot.md), then inspect the desktop using the installed optional dependencies:

```bash
.venv/bin/python scripts/webmind_screenshot.py resolution --json
.venv/bin/python scripts/webmind_screenshot.py full --output desktop.png --json
```

In PowerShell, replace `.venv/bin/python` with `.\.venv\Scripts\python.exe`. These desktop captures differ from Core's page-viewport screenshot. Before acting, read the [mouse guide](../references/mouse.md) or [typing guide](../references/typing.md), confirm the active window, map screenshot coordinates to the primary-screen mouse coordinates, and verify focus.

Choose coordinates and keys from the observed UI rather than a saved screenshot. Desktop text input supports ASCII keyboard-layout characters; use Core `fill` or `insert-text` for non-ASCII text in a webpage. Stay within the user's requested action and return to Core after clearing the native UI.

If the next step depends on asynchronous state, use an appropriate Core selector wait. For a desktop, file, or process condition, follow the [wait guide](../references/wait.md): short waits, a fresh observation after each wait, and a bounded deadline. Time passing does not establish success.

## Verify, then distill the lesson

Check evidence that matches the user's requested result: actual page content, a saved field, a validation message, or the relevant confirmation. A dispatched click, verified focus, or matching immediate field value does not prove that the application accepted the final action. Check whether it already succeeded before retrying an action with side effects.

Once the outcome is understood, retain only a useful reusable lesson: applicable page/task, observed method, verification evidence, date, and limitations. Do not retain credentials, cookies, session URLs, or unrelated private content. Existing host memory permissions determine whether the lesson may be persisted; otherwise present it in the current response.

For an authorized persistent write, this POSIX example creates a candidate note from text supplied on stdin. Replace the template with actual observations first:

```bash
python3 scripts/webmind_memory.py record --task web-reading --file memory.md --title "Reading pattern" --status candidate --stdin --json <<'NOTE'
Template only: replace this text with the applicable page/task, observed method,
outcome evidence, observation date, and remaining limitations.
NOTE
```

The [memory guide](../references/memory.md) covers record options and stdin input. `--status verified` requires `--verified-on` and `--evidence`, but these are recorded declarations, not automatic verification. The host must assess whether a lesson is still applicable; expiry metadata does not automatically invalidate it.

Keep the experience store outside the public repository. WebMind provides the file-management commands and workflow; it does not autonomously learn, validate experience, or authorize future actions.
