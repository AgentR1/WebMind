# WebMind

**A standalone browser skill for AI coding agents, powered by Chrome DevTools Protocol.**

[简体中文](README.zh-CN.md) · [Skill instructions](SKILL.md) · [Command reference](references/commands.md) · [Reading workflows](examples/reading-workflows.md)

WebMind gives a host agent a small Python CLI to inspect and operate a dedicated Chrome or Chromium browser. The host's language model chooses actions and interprets results; WebMind supplies the browser controls. It includes no AI model and requires no third-party Python packages.

## Features

- Reuse a persistent browser profile with its own login state and cookies.
- Read page text, headings, and links with `read-page`; use JavaScript for custom DOM queries.
- List tabs, select a unique page target, and navigate with explicit status reporting.
- Wait for selectors, click elements, fill fields, insert text, and press keys.
- Capture viewport PNG screenshots and handle JavaScript dialogs.
- Return JSON for agent workflows through 13 focused commands.

## Requirements

Python 3.10+, Git, and Chrome or Chromium. Browser discovery covers common macOS, Linux, and Windows locations, including Edge on Windows. Availability of discovery paths is not a claim that every platform/browser combination has been tested. Set `WEBMIND_CHROME` when discovery does not find your executable.

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

## Configuration

Global options go **before the command**; put `--json` at the end.

| Setting | Default | Override |
| --- | --- | --- |
| CDP endpoint | `http://127.0.0.1:9222` | `--endpoint` |
| Browser executable | Common system locations | `--chrome-path` or `WEBMIND_CHROME` |
| Persistent profile | `chrome-profile/` inside the skill | `--user-data-dir` or `WEBMIND_PROFILE` |
| Automatic launch | Enabled for tab commands | `--no-auto-launch` |

Command-line paths take precedence over environment variables. The dedicated profile stores browser state separately from your everyday browser profile. Keep its contents private.

```bash
python3 scripts/webmind.py --endpoint http://127.0.0.1:9334 launch --json
python3 scripts/webmind.py --endpoint http://127.0.0.1:9334 tabs --json
python3 scripts/webmind.py --endpoint http://127.0.0.1:9334 --no-auto-launch self-check --json
```

Use the same endpoint for subsequent commands. `9334` is an example alternative when `9222` is occupied. Close the dedicated browser before relaunching the same profile on another port, or select a separate profile with `--user-data-dir`.

WebMind expects the HTTP CDP discovery endpoints `/json/version` and `/json/list`. Enabling remote debugging through `chrome://inspect/#remote-debugging` in your everyday browser does not necessarily expose those endpoints. Use WebMind's dedicated profile and launch command for this workflow.

The launcher binds debugging to loopback by default. The Python CDP connection bypasses system/environment proxies; page traffic still follows the browser's network configuration. Keep the debugging endpoint local because it controls the browser session.

## Commands and boundaries

The commands are `self-check`, `tabs`, `launch`, `read-page`, `eval`, `navigate`, `wait-for-selector`, `click`, `fill`, `insert-text`, `press`, `screenshot`, and `handle-js-dialog`. See the [command reference](references/commands.md) for options and result fields.

- Prefer `--target-id` from an observed entry with `type: "page"`. Target selection requires a unique matching page; ambiguous matches and non-page targets are rejected.
- Navigation reports `loaded`, `same-document`, `dispatched`, `failed`, `download`, or `timeout`. Navigation errors and wait timeouts return `ok: false` with a nonzero exit code. A load event does not establish that dynamic content is ready.
- Input commands report `status: "dispatched"` and `outcome_verified: false` when issued successfully. A fill's `immediate_value_verified: true` only checks the immediate field value. Read the resulting DOM, validation message, or page state to verify the website's outcome.
- `read-page` takes a heuristic snapshot of the current document. It can miss content or choose the wrong region; inspect its extraction and truncation metadata. It does not perform OCR, extract through iframes or Shadow DOM, or bypass login and access restrictions.
- Screenshots capture the page viewport, not the full document or desktop.
- Native file pickers, browser permission bubbles, extension UI, and OS dialogs are outside the CLI's scope. The host may use its available GUI tools when needed. No other skill package is required.
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

These controlled tests check extraction and browser behavior, including failure cases. They are separate from an end-to-end benchmark on public websites and do not establish a general website task success rate.

An optional [GitHub Actions template](examples/github-actions-checks.yml) runs the offline tests on macOS, Linux, and Windows with Python 3.10 and 3.12. To enable it, copy the template to `.github/workflows/checks.yml` using a GitHub account or token with workflow permissions. The template does not run automatically from `examples/`.

## License and origin

Released under the [MIT License](LICENSE).

WebMind originates from the `webuse_cdp` component of the WebUse toolkit, adapted here into a standalone skill distribution.
