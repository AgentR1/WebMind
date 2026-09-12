# WebMind macOS / Codex User Guide

This guide applies only to **Codex on macOS**. Download or clone the complete repository; the code, launchers, dependencies, and documentation are self-contained and do not require a separate distribution directory.

Before first use, read the [Safety Instructions](Safety%20Instructions.md) in the same directory. This project can change webpages, account state, and desktop state. Its safety constraints cannot guarantee that the model will never make a mistake. Installing dependencies, granting system permissions, and accepting first-use initialization risk are separate actions and do not substitute for one another.

Chinese version: [使用教程](%E4%BD%BF%E7%94%A8%E6%95%99%E7%A8%8B.md).

## 1. What the project can do

The project provides six categories of capability: CDP browser control, desktop screenshots, mouse input, keyboard input, bounded waiting, and external Mem. The recommended execution order is: read relevant Mem -> prefer CDP/DOM -> use desktop tools only when necessary -> verify the result -> reconcile reusable knowledge.

Browser buttons, form input, and page text usually do not require a screenshot first. CDP can inspect the DOM, locate elements with selectors, and send browser input events. File pickers, system dialogs, browser permission bubbles, and similar surfaces are outside the page DOM and require desktop tools. Desktop coordinate actions must be based on an actual current screenshot, not historical coordinates alone.

This package does not include a browser, a signed-in Profile, user Mem, a Python virtual environment, or account credentials. It is also not a remote-control service: Codex, native Python, and the target browser must be on the same macOS computer with a visible desktop session.

## 2. Installation and loading

### 2.1 Prepare the environment

Prepare local Codex, Python 3.10 or newer, and an installed Chrome, Chromium, or Edge browser. The first dependency installation requires internet access. Keep the full repository together; do not copy only one component, and do not move a virtual environment between computers.

If Codex CLI is not installed yet, follow the [official OpenAI Codex CLI documentation](https://learn.chatgpt.com/docs/codex/cli) to install it on macOS, then run `codex` and sign in:

```bash
curl -fsSL https://chatgpt.com/codex/install.sh | sh
codex
```

You can also send the following instruction to Codex running on the Mac and provide the real absolute path to the repository root:

```text
Please inspect and install the WebMind project in this directory. Read the User Guide and Safety Instructions first, verify the local environment, and then follow the appropriate installation steps. Ask for my permission before installing software, changing configuration, or requesting additional permissions. Do not automatically disable sandboxing or change system security policies.
```

### 2.2 Manual installation

Open Terminal, enter the complete repository directory, and install:

```bash
cd "/path/to/webmind-codex"
python3 --version
bash './scripts/install.sh'
bash "$HOME/.agents/skills/webmind-codex/scripts/webmind.sh" doctor --json
```

Replace `/path/to/webmind-codex` with the real repository path. By default, the Skill is installed at `~/.agents/skills/webmind-codex`, runtime dependencies are stored in `~/Library/Application Support/WebMindCodex/.venv`, and the Mem location is selected separately during first-use initialization. This matches the user-level Skill directory described in the [official Skill documentation](https://learn.chatgpt.com/docs/build-skills).

After installation, invoke it explicitly with `$webmind-codex` and confirm that the Skill is discovered. Codex usually detects Skill changes automatically; if it does not appear, restart Codex.

### 2.3 Unified entry point for later commands

The initialization, diagnostic, and browser examples below use `webmind` as a temporary shell function in the current Terminal session. Set the real path and define the function first. You must define it again after opening a new shell. The installer does not install a global `webmind` command.

```bash
WEBMIND_ROOT="$HOME/.agents/skills/webmind-codex"
webmind() { bash "$WEBMIND_ROOT/scripts/webmind.sh" "$@"; }
```

An Agent should resolve the root directory from the Skill or plugin path that was actually discovered and invoke the full launcher path under that root instead of assuming this temporary shell function exists.

### 2.4 Optional installation arguments

`scripts/install.py` supports user-scoped, project-scoped, and custom-directory installation. Append these options to the installation command for this edition:

```text
--scope project --project <absolute-project-path>
--data-dir <external-python-runtime-directory>
--add-agent-rules
--dry-run
--skip-deps
```

Project-scoped installation places the Skill under `.agents/skills/webmind-codex` in that project. `--data-dir` selects the location for the Python runtime and related data and records it in installation metadata; it does not replace Mem selection. `--add-agent-rules` writes bounded routing rules only when explicitly requested and preserves a backup; by default the installer does not modify global Codex instructions or configuration.

`--dry-run` only shows the installation plan. `--skip-deps` only copies source files and does not mean dependencies or GUI permissions are ready. Do not enable multiple installations with the same Skill name without confirming which path is actually active. For a custom runtime directory, `WEBMIND_CODEX_DATA_DIR` takes precedence; the compatibility variable `WEBMIND_DATA_DIR` may also affect resolution, so verify the actual path reported by `doctor` after setting either one.

## 3. First-use initialization: choose an external Mem

Installation does not mean initialization is complete. Before the first real browser or desktop task, the Agent checks initialization, recommends this guide and the Safety Instructions, explains that residual risk remains, and asks whether you accept the risk and want to continue. **The Agent must not pass `--accept-risk` until you explicitly agree.**

Choose a parent directory outside all Skill, plugin, and source directories. It can be Downloads, Desktop, Documents, or a dedicated user-data directory. Do not place active Mem inside this distribution. After you choose a parent, only its direct children are scanned; the entire disk is not searched recursively. If reusable Mem folders are found, you decide whether to reuse one.

A new Mem name must use the form `xxx-yyy-mem`: `xxx` is 1-8 lowercase English letters, `yyy` is an integer from 1 to 999 with no leading zero, and the `-mem` suffix is mandatory. For example, `work-42-mem` maps to port **1042**, because the port is always `1000 + yyy`.

**When creating a new Mem, both `xxx` and `yyy` must each be unique on this Mac. Do not reuse either value from any other WebMind Mem.**

After accepting the risk and choosing the parent and name, you can initialize manually:

```bash
MEM_PARENT="$HOME/WebMindData"
mkdir -p "$MEM_PARENT"
webmind mem scan --parent "$MEM_PARENT" --json
webmind mem name-info --name work-42-mem --json
webmind mem init --mem-path "$MEM_PARENT/work-42-mem" --accept-risk --json
```

The external directory structure is:

```text
work-42-mem/
  global.md
  content.md
  work-42-mem-Profile/
    webmind-profile.json
    ...browser-owned data...
  task-category/
    memory.md
    flow.md
    ui.md
    rules.md
    notes.md
```

For a new Mem, `global.md` is copied from the bundled `basic-rules.md`. When attaching to an existing Mem, its existing `global.md` is preserved. The browser directory is exactly `<Mem-name>-Profile` inside the corresponding Mem. Its `webmind-profile.json` records the absolute profile path, loopback address, and port. CDP must read and verify that metadata before launching or connecting.

Inside the Skill, only the selected Mem location pointer at `components/webmind-mem/mem-location.json` is recorded. Active Mem contents and browser sessions are not stored in the Skill. Browser Profile contents are excluded from Mem indexing, search, and summarization.

Remember the Mem name and location. Normal later tasks should not ask again. After an update or plugin reload, if the location pointer is missing, reselect the existing Mem instead of creating a new one and assuming the old knowledge disappeared. To switch Mem or dedicated browser, re-enter initialization before or after a task; do not temporarily bypass configuration with `--endpoint` or `--user-data-dir`.

**On the same Mac, every WebMind Mem should use a unique `xxx` and a unique `yyy`; do not reuse either value.** `yyy` directly determines the debugging port `1000 + yyy`, so reusing `yyy` also creates a port collision. The program will not resolve such a conflict by closing another browser.

## 4. Environment and browser checks

Run these commands in order:

```text
webmind doctor --json
webmind mem init-status --json
webmind mem check --json
webmind cdp self-check --json
```

If the browser is not running yet, a failing `cdp self-check` does not necessarily mean the installation is broken; this command checks the connection and does not open the browser. After initialization, you can launch it explicitly:

```text
webmind cdp launch --url https://example.com --json
webmind cdp tabs --json
webmind cdp self-check --json
```

Before each Agent command that may open the browser, the Agent should state that it is opening the CDP browser dedicated to the Agent, then continue with the task. This notice is informational and is not an extra confirmation prompt. If the actual browser is Edge or another supported browser, use its real name.

Pay particular attention to `profile_verified`, the actual Profile, and the target tab. A reachable port, a correct page title, or a successful launch result alone does not prove that the correct browser was connected. Initialization state, dependency readiness, OS permissions, and browser availability must also be checked separately.

### macOS environment notes

This edition includes the repaired LaunchServices launch path. CDP automatically invokes the bundled `launch_chrome_macos.sh`, which uses `open -na <Browser.app> --args ...` to open the dedicated browser instead of launching the Chrome main process as a short-lived child process. Users do not need to call this helper directly.

Browsers are searched for under `/Applications` and `~/Applications` by default. A custom path can be supplied with `--chrome-path "/Applications/Google Chrome.app"`; this global CDP argument appears before the CDP subcommand. Launch readiness waits for up to 60 seconds by default. A successful `open` call does not mean CDP is ready. On failure, inspect the error and private launch-request log location; do not treat that file as a complete browser log and do not forward unreviewed log contents.

Desktop screenshots require Screen Recording permission for the Terminal, IDE, or host application that actually executes the command. Mouse and keyboard control normally require Accessibility permission. Grant only permissions that are actually needed, manually through System Settings, and restart the host if macOS requires it. Host approval for shell/CDP actions and macOS privacy permissions are two separate permission layers; do not let the Agent automatically modify either one.

Apple Silicon and Intel Macs should each use native Python for their architecture. Do not copy `.venv` between architectures. Retina screenshots use image pixels while mouse coordinates use logical points. Convert with `x = region.left + image_x / image.scale_x`, and likewise for y. With mixed-scaling multi-monitor setups, prefer a single-display screenshot region.

Codex command approvals still apply. The LaunchServices fix does not automatically grant access outside the sandbox and does not promise that every session will require only one approval. If access is denied, use Codex's normal and narrowest available authorization flow. Do not switch shells or tools to bypass a denial. See the [official OpenAI sandboxing documentation](https://learn.chatgpt.com/docs/sandboxing).

## 5. Tabs and webpage operations

When multiple pages are open, run `tabs` first, obtain the real IDs, and use the correct `--target-id` for later actions. `TARGET` in the examples must be replaced with the actual ID.

```text
webmind cdp --no-auto-launch new-tab --url https://example.com --json
webmind cdp --no-auto-launch switch-tab --target-id TARGET --json
webmind cdp --no-auto-launch close-tab --target-id TARGET --json
webmind cdp --no-auto-launch eval --target-id TARGET --expression "document.title" --json
webmind cdp --no-auto-launch wait-for-selector --target-id TARGET --selector "main" --visible --timeout 10 --json
```

`new-tab` creates a page. `switch-tab` activates an existing page and requests that it be brought forward without creating or closing a tab. `close-tab` closes only the specified page and refuses to close the final page tab to avoid closing the entire browser. The operating system may still prevent a window from stealing focus, so verify real window focus before any global keyboard action.

`--no-auto-launch` is useful when reusing an already connected and verified browser. If the connection is lost, it fails instead of silently opening a new window. Before actions such as sending, deleting, publishing, or uploading, still verify the user-authorized target and content. Do not treat a timeout as proof that the action did not occur and then blindly submit it again.

### Non-sensitive Chinese and complex text

Prefer CDP `fill` / `insert-text`. Desktop `typing type` supports printable ASCII only and is not responsible for Chinese input methods. `fill` sets a field and dispatches input events; `insert-text` inserts text through the browser input interface. Complex sites still require verification of the actual result.

The Codex unified launcher supports UTF-8 `--input-file` for non-sensitive Chinese or multiline text:

```text
webmind cdp --no-auto-launch fill --target-id TARGET --selector "textarea" --input-file <absolute-path-to-non-sensitive-UTF8-file> --json
webmind cdp --no-auto-launch eval --target-id TARGET --input-file <absolute-path-to-UTF8-script> --json
```

`--input-file` is implemented by the unified launcher and must not be passed directly to a component script. Replace example paths and selectors with values verified for the current task.

These methods are only for non-sensitive content. Passwords, verification codes, tokens, payment data, and similar secrets must not be written to arguments, input files, logs, or the clipboard. Enter them yourself in the target page. File reading and screenshots do not substitute for authorization to use the content.

## 6. Two usage modes

### 6.1 Recommended: dedicated CDP browser bound to Mem

This mode uses a browser already installed on the computer but with a separate persistent Profile stored inside the selected Mem instead of the everyday default Profile. It is well suited for repeated web tasks, DOM inspection, and reducing coordinate-based interaction and screenshots.

```text
$webmind-codex Please use the dedicated CDP browser for this task. Read the selected Mem before starting, verify the result, and reconcile verified reusable knowledge afterward. Do not send, delete, upload, or publish anything without my explicit authorization. The task is...
```

The first visit to a website that requires authentication may require you to sign in manually. If the website does not invalidate the session and the Profile is not cleared, later tasks can often reuse the signed-in state, but permanent login is not guaranteed. Do not copy a currently running everyday Profile directly into the automation browser.

### 6.2 Explicit alternative: operate the everyday browser you already opened

This mode primarily uses desktop screenshots, mouse, and keyboard, and does not attach the everyday default Profile to CDP. It generally needs more visual verification and is more sensitive to layout, focus, and display scaling. The project's first-use risk acceptance and Mem initialization are still required.

```text
$webmind-codex Do not use CDP for this task; operate the everyday browser I already have open. Read relevant Mem first, verify the actual screenshot and mouse position before every desktop click, and reconcile reusable knowledge afterward. The task is...
```

Do not broaden the Codex workspace or host permissions merely because CDP can connect to a website. The user still defines the authorized target and scope for actions with external effects such as sending, deleting, publishing, or uploading.

## 7. Usage recommendations

### Start with low-risk tasks

Good first tests include opening a public page and reading its title, searching public articles and summarizing them, or typing test text into a blank editor. Do not begin with payment, deletion, account permissions, or important files.

### Give clear task boundaries

Email example: "In Gmail, draft an invitation email to the specified recipient and save it as a draft only. Do not send it. Verify the recipient first."

Public-web example: "Search for public articles about the specified topic, read relevant body text, and summarize it. Save the result to the directory I specify. Do not sign in and do not download executable files."

External-effect example: "Prepare the content for submission. Before the final send or publish action, show me the target and content and wait for my confirmation, then perform the action once." The scope of the original task authorization always takes precedence; an existing signed-in session does not expand authorization.

### When the first task is slow, you can teach the model

Model capability, page complexity, and website changes can all affect first-run speed. You can explain the relative location of a field and button, whether a button previews or submits immediately, which category must be selected first, or which field becomes available afterward. These instructions must not contain passwords, tokens, or other secrets, and must not expand the authorized scope.

At task end, the Agent reviews whether any verified reusable knowledge was learned and reconciles it with existing Mem, removing duplicate or obsolete methods. Keeping the Mem and reading it next time may reduce repeated exploration, but does not guarantee every task will be faster. A claim that something was "saved to memory" is valid only after the write actually succeeds.

### If a search engine rejects automated search

A rejected search query does not mean a known official website cannot be opened directly. You can manually take over and complete verification, ask the model to use another search engine in the **same browser and same Profile**, or open a known official site directly. Do not automatically defeat CAPTCHA, clear login data, rebuild the Profile, or switch control mechanisms merely because search was rejected.

### Keep desktop automation observable and interruptible

Do not switch windows or type at the same time as desktop automation. Keep the PyAutoGUI failsafe enabled. To stop, prefer the host application's stop control or move the mouse to a failsafe corner. This cannot undo an external action that already completed and does not guarantee interruption of every in-flight CDP request.

## 8. Common failures

| Symptom | Check first |
| --- | --- |
| Initialization required | Run `mem init-status`; follow the risk-acceptance and path-selection flow instead of editing the pointer manually. |
| Profile or port mismatch | Check the current Mem name and `webmind-profile.json`; do not take over another browser. |
| Cannot connect after launch | Inspect the error, port conflicts, Profile lock, and host approval; do not delete the Profile first. |
| Screenshot works but clicks are misplaced | Recheck the current display layout, screenshot region, image scaling, and actual mouse position. |
| Text goes into Terminal | Stop first, then re-verify the target application and input focus; do not blindly continue with Enter. |
| Chinese text is garbled | Verify UTF-8 files/pipes and use the matching CDP text path instead of simulating an ASCII keyboard input method. |
| Old knowledge is missing after an update | Find the original external Mem and reselect it through initialization; do not replace it with a new Mem and then delete the old directory. |

If an incorrect send, delete, upload, or other major unintended result has already occurred, stop at the nearest safe point. Perform only necessary read-only checks and report what happened. Do not automatically refresh, retry, undo, or clean up.

## 9. Updates, removal, and backup

Before upgrading, finish the current task, back up source modifications, and remember the external Mem location. Removing the code does not sign out website sessions; Profiles containing signed-in state still need to be managed by you. Do not package and share an entire Mem as if it were ordinary knowledge, because it also contains browser data.

Even reusable knowledge should be reviewed and redacted before sharing. Share only genuinely non-sensitive task Markdown. Do not include Profiles, location pointers, cookies, caches, screenshots, or temporary input files.

## 10. Compatibility scope and references

GitHub release checks only verify that Python source compiles, the installer can produce an installation plan, dependencies can be installed, and Shell scripts pass syntax checks. They do not operate a real desktop and cannot replace acceptance testing on the target Mac for permissions, displays, browser startup, signed-in state, or focus. Begin with a low-risk read-only task and inspect the actual results of `doctor`, `mem init-status`, `mem check`, and `cdp self-check`. See [Reference Sources](references/SOURCES.md) for official host documentation.
