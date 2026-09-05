# WebMind

**A standalone browser skill for AI coding agents, powered by Chrome DevTools Protocol.**

[简体中文](README.zh-CN.md) · [Skill instructions](SKILL.md) · [Command reference](references/commands.md)

WebMind gives a host agent a small Python CLI to inspect and operate a dedicated Chrome or Chromium browser. The host's language model chooses actions and interprets results; WebMind supplies the browser controls. It includes no AI model and requires no third-party Python packages.

## Features

- Reuse a persistent browser profile with its own login state and cookies.
- List tabs, select a target, navigate, and read the DOM with JavaScript.
- Wait for selectors, click elements, fill fields, insert text, and press keys.
- Capture viewport PNG screenshots and handle JavaScript dialogs.
- Return JSON for agent workflows through 12 focused commands.

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

Copy the intended page's `id` from `tabs`, replace `TAB_ID` below, then navigate and read it:

```bash
python3 scripts/webmind.py navigate --target-id TAB_ID --url "https://example.com" --wait-load --json
python3 scripts/webmind.py wait-for-selector --target-id TAB_ID --selector "h1" --visible --json
python3 scripts/webmind.py eval --target-id TAB_ID --expression "({title: document.title, url: location.href, text: document.body.innerText})" --json
python3 scripts/webmind.py screenshot --target-id TAB_ID --output page.png --json
```

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

The commands are `self-check`, `tabs`, `launch`, `eval`, `navigate`, `wait-for-selector`, `click`, `fill`, `insert-text`, `press`, `screenshot`, and `handle-js-dialog`. See the [command reference](references/commands.md) for options and examples.

- Prefer `--target-id` from an observed entry with `type: "page"`. Automatic selection prefers page targets but can fall back to another debuggable target if no page is available; URL/title filters select the first match.
- A successful `click` or `fill` response confirms the operation was issued, not that the website accepted it. Read the resulting DOM, field value, or page state to verify the outcome.
- A load event does not guarantee that dynamic content is ready. Wait for the needed selector or inspect page state.
- Screenshots capture the page viewport, not the full document or desktop.
- Native file pickers, browser permission bubbles, extension UI, and OS dialogs are outside the CLI's scope. The host may use its available GUI tools when needed. No other skill package is required.
- Browser actions remain subject to the user's request and the host agent's authorization rules.

## Tests

Run the unit suite from the repository root:

```bash
python3 -m unittest discover -s tests -v
```

Browser integration tests are opt-in:

```bash
WEBMIND_TEST_CHROME=/absolute/path/to/chrome python3 -m unittest discover -s tests -v
```

In PowerShell:

```powershell
$env:WEBMIND_TEST_CHROME = "C:\path\to\chrome.exe"
py -3 -m unittest discover -s tests -v
```

An optional [GitHub Actions template](examples/github-actions-checks.yml) runs the offline tests on macOS, Linux, and Windows with Python 3.10 and 3.12. To enable it, copy the template to `.github/workflows/checks.yml` using a GitHub account or token with workflow permissions. The template does not run automatically from `examples/`.

## License and origin

Released under the [MIT License](LICENSE).

WebMind originates from the `webuse_cdp` component of the WebUse toolkit, adapted here into a standalone skill distribution.
