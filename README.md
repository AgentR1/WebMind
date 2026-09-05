# WebMind

**One skill for browser control, desktop interaction, and reusable local experience.**

[简体中文](README.zh-CN.md) · [Skill instructions](SKILL.md) · [Browser commands](references/commands.md) · [Reading workflows](examples/reading-workflows.md) · [Full workflow](examples/full-workflow.md)

WebMind is a complete automation skill suite for AI coding agents, exposed through a single `$webmind` entry point. Its six modules cover a dedicated Chrome or Chromium browser, local experience files, screenshots, mouse control, keyboard input, and waiting. The host's language model chooses actions and interprets results; WebMind provides instructions and tools, not an AI model.

## Six modules

| Module | What it provides | Reference |
| --- | --- | --- |
| Core | 13 CDP commands for tabs, navigation, page reading, DOM interaction, viewport screenshots, and JavaScript dialogs; persistent browser sessions. | [Browser commands](references/commands.md) |
| Experience (Memory) | Initialize, check, index, search, read, and record local experience files, including global and task-specific notes. | [Memory guide](references/memory.md) |
| Screenshot | Desktop resolution and full-screen, half-screen, or region captures. | [Screenshot](references/screenshot.md) |
| Mouse | Position, movement, clicks, dragging, and scrolling. | [Mouse](references/mouse.md) |
| Typing | ASCII text input, individual keys, held keys, and keyboard shortcuts. | [Typing](references/typing.md) |
| Wait | Short wait-and-inspect loops for UI, processes, and other readiness signals. | [Wait](references/wait.md) |

Use Core for ordinary webpage work and desktop tools for native or visual-only surfaces. Experience provides file management; selecting useful lessons, checking their applicability, and verifying outcomes remain the host agent's work. There is no automatic learning or automatic experience-verification engine.

## Requirements

Python 3.10+ and Git. Core browser work also needs Chrome or Chromium. Core and Experience (Memory) use only the Python standard library; desktop tools have optional dependencies listed below. Browser discovery covers common macOS, Linux, and Windows locations, including Edge on Windows. Availability of discovery paths is not a claim that every platform/browser combination has been tested. Set `WEBMIND_CHROME` when discovery does not find your executable.

## Install

Choose the skill directory for your host. For Codex on macOS or Linux:

```bash
mkdir -p "$HOME/.codex/skills"
git clone https://github.com/AgentR1/WebMind.git "$HOME/.codex/skills/webmind"
cd "$HOME/.codex/skills/webmind"
```

For Claude Code, use `~/.claude/skills/webmind` instead:

```bash
mkdir -p "$HOME/.claude/skills"
git clone https://github.com/AgentR1/WebMind.git "$HOME/.claude/skills/webmind"
cd "$HOME/.claude/skills/webmind"
```

Windows PowerShell, for Codex:

```powershell
New-Item -ItemType Directory -Force "$HOME/.codex/skills" | Out-Null
git clone https://github.com/AgentR1/WebMind.git "$HOME/.codex/skills/webmind"
Set-Location "$HOME/.codex/skills/webmind"
```

For Claude Code in PowerShell, replace `.codex` with `.claude` in those commands. The examples below run from the installed skill directory. On Windows, use `py -3` in place of `python3` with Python 3.10 or newer installed.

### Optional desktop dependencies

Install `mss`, Pillow, and PyAutoGUI in a local virtual environment when desktop capture or input is needed. On macOS or Linux:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-desktop.txt
.venv/bin/python scripts/webmind_screenshot.py self-check --json
```

Windows PowerShell:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-desktop.txt
.\.venv\Scripts\python.exe scripts/webmind_screenshot.py self-check --json
```

Use that environment's interpreter for the screenshot, mouse, and typing scripts. Desktop operation also requires an interactive graphical session and any screen-recording/accessibility permissions required by the OS. Read the relevant module guide before using it; installing dependencies does not establish that desktop access works.

## Quickstart

In your host agent, invoke the skill with a concrete request, for example:

> Use $webmind to open https://example.com and report the page title and main text.

Or use the CLI directly:

```bash
python3 scripts/webmind.py launch --json
python3 scripts/webmind.py tabs --json
```

Copy the intended `type: "page"` entry's `id` from `tabs`, replace `TAB_ID` below, then navigate and read it:

```bash
python3 scripts/webmind.py navigate --target-id TAB_ID --url "https://example.com" --wait-load --json
python3 scripts/webmind.py read-page --target-id TAB_ID --wait-selector "h1" --max-chars 20000 --max-links 100 --json
python3 scripts/webmind.py screenshot --target-id TAB_ID --output page.png --json
```

`read-page` returns the page title, URL, language, extracted text, headings, and deduplicated HTTP(S) links, together with extraction and truncation metadata. It chooses a likely main-content region heuristically; use `--selector` to read a specific observed region and `eval` for custom DOM queries. See [reading workflows](examples/reading-workflows.md) for login sessions, dynamic content, and recovery examples.

`launch` reuses a responding endpoint. Its `--url` only applies when starting a browser, so use `navigate` to open a URL reliably on an existing target. `tabs` and target commands can launch the dedicated browser automatically when the local endpoint is unavailable. `self-check` only checks the endpoint.

For a concrete web task, use the [Memory guide](references/memory.md) to select relevant prior experience before acting. After verifying the result, record reusable lessons only when the host's memory permissions allow it. Experience is a hint to check against the current page, not authorization to send, publish, purchase, or perform other external actions. The [full workflow](examples/full-workflow.md) shows how the modules fit together.

## Configuration

For the Core CLI, global options go **before the command**; put `--json` at the end.

| Setting | Default | Override |
| --- | --- | --- |
| CDP endpoint | `http://127.0.0.1:9222` | `--endpoint` |
| Browser executable | Common system locations | `--chrome-path` or `WEBMIND_CHROME` |
| Persistent profile | `chrome-profile/` inside the skill | `--user-data-dir` or `WEBMIND_PROFILE` |
| Automatic launch | Enabled for tab commands | `--no-auto-launch` |
| Experience store | `~/.local/share/webmind/Mem` | Memory CLI `--mem-path` or `WEBMIND_MEM` |

Command-line paths take precedence over environment variables. The dedicated profile stores browser state separately from your everyday browser profile. Experience files live outside the skill repository by default. Keep private browser state and personal experience out of public commits; the repository supplies tools and examples, not personal memory.

```bash
python3 scripts/webmind.py --endpoint http://127.0.0.1:9334 launch --json
python3 scripts/webmind.py --endpoint http://127.0.0.1:9334 tabs --json
python3 scripts/webmind.py --endpoint http://127.0.0.1:9334 --no-auto-launch self-check --json
```

Use the same endpoint for subsequent commands. `9334` is an example alternative when `9222` is occupied. Close the dedicated browser before relaunching the same profile on another port, or select a separate profile with `--user-data-dir`.

WebMind expects the HTTP CDP discovery endpoints `/json/version` and `/json/list`. Enabling remote debugging through `chrome://inspect/#remote-debugging` in your everyday browser does not necessarily expose those endpoints. Use WebMind's dedicated profile and launch command for this workflow.

The launcher binds debugging to loopback by default. The Python CDP connection bypasses system/environment proxies; page traffic still follows the browser's network configuration. Keep the debugging endpoint local because it controls the browser session.

## Commands and boundaries

The Core commands are `self-check`, `tabs`, `launch`, `read-page`, `eval`, `navigate`, `wait-for-selector`, `click`, `fill`, `insert-text`, `press`, `screenshot`, and `handle-js-dialog`. See the [browser command reference](references/commands.md) for options and result fields; the other modules have their own guides above.

- Prefer `--target-id` from an observed entry with `type: "page"`. Target selection requires a unique matching page; ambiguous matches and non-page targets are rejected.
- Navigation reports `loaded`, `same-document`, `dispatched`, `failed`, `download`, or `timeout`. Navigation errors and wait timeouts return `ok: false` with a nonzero exit code. A load event does not establish that dynamic content is ready.
- Input commands report `status: "dispatched"` and `outcome_verified: false` when issued successfully. A fill's `immediate_value_verified: true` only checks the immediate field value. Read the resulting DOM, validation message, or page state to verify the website's outcome.
- `read-page` takes a heuristic snapshot of the current document. It can miss content or choose the wrong region; inspect its extraction and truncation metadata. It does not perform OCR, extract through iframes or Shadow DOM, or bypass login and access restrictions.
- Core screenshots capture the page viewport. The Screenshot module captures desktop screens and regions; neither is an automatic full-document capture tool.
- Native file pickers, browser permission bubbles, extension UI, and OS dialogs require desktop interaction. First inspect a desktop screenshot, then use the Mouse/Typing guides or suitable host GUI tools, and return to Core when the page is accessible.
- Desktop mouse coordinates use the primary screen and may differ from screenshot/DPI coordinates. Confirm the mapping and keyboard focus; use Core `fill` or `insert-text` for non-ASCII webpage text.
- Browser actions remain subject to the user's request and the host agent's authorization rules.

## Tests

Run the unit suite from the repository root:

```bash
python3 -m unittest discover -s tests -v
```

Browser integration tests are opt-in. They exercise task scenarios in a real Chrome browser against a local HTTP test site:

```bash
WEBMIND_TEST_CHROME=/absolute/path/to/chrome python3 -m unittest discover -s tests -v
```

In PowerShell:

```powershell
$env:WEBMIND_TEST_CHROME = "C:\path\to\chrome.exe"
py -3 -m unittest discover -s tests -v
```

These controlled tests check extraction and browser behavior, including failure cases. They are separate from an end-to-end benchmark on public websites and do not establish a general website task success rate. Passing offline tests also does not establish desktop permissions or successful mouse/keyboard control on a live OS session.

An optional [GitHub Actions template](examples/github-actions-checks.yml) runs the offline tests on macOS, Linux, and Windows with Python 3.10 and 3.12. To enable it, copy the template to `.github/workflows/checks.yml` using a GitHub account or token with workflow permissions. The template does not run automatically from `examples/`.

## License and origin

Released under the [MIT License](LICENSE).

WebMind originates from the WebUse toolkit, including its browser, memory, screenshot, mouse, typing, and wait components, adapted and extended here as one standalone skill suite.
