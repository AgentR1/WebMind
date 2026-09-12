# WebMind Windows / Claude Code User Guide

Chinese version: [使用教程](使用教程.md)

This guide applies only to **Claude Code on Windows**. After cloning the repository or downloading a GitHub Release, the code, launchers, dependency declarations, and documentation in this project can be used independently.

Before first use, read the [Safety Instructions](SAFETY_INSTRUCTIONS.md) in the same directory. This project can change web pages, account state, and desktop state; its safety constraints cannot guarantee that the model will never make a mistake. Installing dependencies, granting system permissions, and accepting the first-run initialization risk are separate actions and do not replace one another.

## 1. What the project can do

The project provides six capabilities: CDP browser control, desktop screenshots, mouse control, keyboard control, bounded waiting, and external Mem storage. The recommended execution order is: read relevant Mem -> prefer CDP/DOM -> use desktop tools only when necessary -> verify the result -> reconcile reusable knowledge.

Locating web buttons, entering text, and reading page content usually do not require a screenshot first: CDP can inspect the DOM, locate elements by selector, and dispatch browser input events. File pickers, system dialogs, browser permission bubbles, and other native UI are outside the page DOM and require desktop tools. Desktop coordinate operations must be based on a current screenshot, not historical coordinates alone.

This package does not include a browser binary, signed-in profiles, user Mem data, a Python virtual environment, or account credentials. It is also not a remote-control service: Claude Code, native Python, and the target browser must run on the same Windows machine with a visible desktop session.

## 2. Installation and loading

### 2.1 Prepare the environment

Prepare local Claude Code, Python 3.10 or newer, and an installed Chrome / Chromium / Edge browser. Internet access is required the first time Python dependencies are installed. Clone the whole repository or fully extract the Release; do not copy only one component, and do not move a virtual environment between machines.

You can also send the following instruction to Claude Code on the target machine and provide the real absolute project-root path:

```text
Please inspect and install the WebMind project in this directory. Read the User Guide and Safety Instructions first, verify the local environment, and then follow the appropriate installation steps. Ask for my approval before installing software, changing configuration, or requesting additional permissions. Do not automatically disable sandboxing or change system security policies.
```

### 2.2 Manual installation

This plugin depends on the complete project root and cannot be installed by copying only one folder under `skills/`. Install the Python dependencies from native PowerShell:

```powershell
$WebMindRoot = 'D:\Tools\windows-claudecode'
& "$WebMindRoot\scripts\install.ps1"
& "$WebMindRoot\scripts\webmind.ps1" doctor --json
claude --plugin-dir "$WebMindRoot"
```

Replace the path with the actual project location. `install.ps1` automatically uses Windows `py -3` or `python`, verifies Python 3.10+, creates `%LOCALAPPDATA%\WebMind\.venv`, and installs dependencies. It does not automatically register the plugin. The final command loads the complete directory through Claude Code's local plugin entry point.[1]

If system policy blocks PowerShell scripts, you can install dependencies and run diagnostics with native Python in the same terminal without changing the execution policy:

```powershell
$DataRoot = Join-Path $env:LOCALAPPDATA 'WebMind'
New-Item -ItemType Directory -Path $DataRoot -Force | Out-Null
python --version
python -m venv (Join-Path $DataRoot '.venv')
& "$DataRoot\.venv\Scripts\python.exe" -m pip install -r "$WebMindRoot\requirements.txt"
& "$DataRoot\.venv\Scripts\python.exe" "$WebMindRoot\scripts\webmind.py" doctor --json
```

Confirm that each step succeeds before continuing. If the system has only the `py` launcher, replace `python` above with `py -3`. Continue to use `claude --plugin-dir "$WebMindRoot"` to load the plugin; do not change host configuration without authorization.

### 2.3 Unified command entry point for later examples

The initialization, diagnostic, and browser examples below use `webmind` as a temporary function in the current terminal. Set the real path and define it first; define it again in a new terminal session. It is not a global command installed by the setup script. This function invokes the virtual environment's Python directly, so it also works when unsigned `.ps1` files are blocked:

```powershell
$WebMindRoot = "D:\Tools\windows-claudecode"
$WebMindData = if ($env:WEBMIND_DATA_DIR) { $env:WEBMIND_DATA_DIR } else { Join-Path $env:LOCALAPPDATA 'WebMind' }
$WebMindPython = Join-Path $WebMindData '.venv\Scripts\python.exe'
function webmind { & $WebMindPython "$WebMindRoot\scripts\webmind.py" @args }
```

The Agent should resolve the project root from the actual discovered Skill or plugin path and invoke the full launcher path under that root instead of assuming that this temporary function already exists.

### 2.4 Optional marketplace installation

The project includes a marketplace that points only to itself. After publishing to GitHub, register and install it using `owner/repository`:

```text
claude plugin marketplace add <GitHub-username>/<repository>
claude plugin install webmind-claudecode@webmind-claudecode
```

For local validation before publishing, the first command can use the absolute project-root path instead of a GitHub repository; quote paths containing spaces. Do not enable the same plugin from multiple sources at the same time. Marketplace installation uses a cached copy, so after loading the plugin, resolve the root from the actual Skill path rather than assuming the source checkout is the runtime location.[2]

This edition still uses `WEBMIND_DATA_DIR` to customize the Python runtime-data directory; ensure the same setting is used in future runs. It does not select the active Mem. On first use, the Agent initializes according to `skills/webmind-mem/SKILL.md` in the active plugin. You can explicitly invoke `/webmind-claudecode:webmind-mem`.

## 3. First initialization: select an external Mem

Installation does not mean initialization is complete. Before the first real browser or desktop task, the Agent checks status, recommends this guide and the Safety Instructions, explains that residual risk remains, and asks whether you accept that risk and want to continue. **The Agent must not use `--accept-risk` until you explicitly agree.**

Choose a parent directory outside every Skill, plugin, and source folder. Downloads, Desktop, Documents, or a dedicated user-data directory are acceptable choices; do not place the active Mem inside this distribution. After you select the parent, only its direct children are scanned. WebMind does not recursively search an entire drive. If valid existing Mem folders are found, you choose whether to reuse one.

A new Mem name must use the form `xxx-yyy-mem`: `xxx` is 1-8 lowercase English letters, `yyy` is an integer from 1 to 999 with no leading zero, and the `-mem` suffix is mandatory. **When initializing a new Mem, the Agent must explicitly tell you that both `xxx` and `yyy` must each be unique: do not reuse an `xxx` or a `yyy` already used by another WebMind Mem on this computer.** `name-info` validates the name format only; it does not prove uniqueness. For example, `work-42-mem` uses port **1042**, because the port is always `1000 + yyy`.

After accepting the risk and choosing the parent and name, you can initialize manually:

```powershell
$MemParent = 'D:\WebMindData'
New-Item -ItemType Directory -Path $MemParent -Force | Out-Null
webmind mem scan --parent $MemParent --json
webmind mem name-info --name work-42-mem --json
webmind mem init --mem-path (Join-Path $MemParent 'work-42-mem') --accept-risk --json
```

The external directory structure is:

```text
work-42-mem/
  global.md
  content.md
  work-42-mem-Profile/
    webmind-profile.json
    ...browser-owned data...
  some-task/
    memory.md
    flow.md
    ui.md
    rules.md
    notes.md
```

For a new Mem, `global.md` is copied from the bundled `basic-rules.md`; when attaching an existing Mem, its existing `global.md` is preserved. The browser directory is exactly `<Mem-name>-Profile` directly inside the corresponding Mem. `webmind-profile.json` inside that Profile records the absolute path, loopback address, and port. CDP must read and verify it before launching or connecting.

The Skill stores only the selected Mem location pointer at `skills/webmind-mem/mem-location.json`; it does not store the active Mem itself or the browser session in the plugin source. Browser Profile contents are excluded from Mem indexing, searching, and summarization.

Remember the Mem name and location. Normal later tasks should not ask again. If the location pointer is missing after updating or reloading the plugin, select the existing Mem again instead of creating a replacement and assuming the old knowledge was lost. To change the Mem or dedicated browser, re-enter initialization before or after a task; do not temporarily bypass configuration with `--endpoint` or `--user-data-dir`.

**On the same computer, do not reuse any existing `xxx` or `yyy` when creating another Mem.** In particular, two different Mem names that reuse the same `yyy` still occupy the same port. The program will not close another browser to resolve a conflict.

## 4. Environment and browser checks

Run these commands in order:

```text
webmind doctor --json
webmind mem init-status --json
webmind mem check --json
webmind cdp self-check --json
```

If the browser is not running yet, a failed `cdp self-check` does not necessarily mean the installation is broken; that command only checks and does not launch the browser. After initialization, you can launch explicitly:

```text
webmind cdp launch --url https://example.com --json
webmind cdp tabs --json
webmind cdp self-check --json
```

Before every command that may open a browser, the Agent should state, "This will open the CDP (Agent-dedicated) Chrome browser," and then continue. This notice is not an additional confirmation request. If the actual browser is Edge or another supported browser, use its real name.

Pay particular attention to `profile_verified`, the actual Profile, and the target tab. A reachable port, the expected page title, or a successful process launch alone does not prove that the correct browser is connected. Initialization state, dependencies, system permissions, and browser availability must be checked separately.

### Windows environment notes

Use native Windows Python and a host that can access the currently logged-in user's desktop. Do not operate the Windows desktop from a WSL Python process. Window focus and desktop-session state must be correct; "the command ran" does not mean the browser received the click or keystroke.

This edition launches the dedicated Profile through the Windows browser executable path and waits up to 10 seconds by default for CDP readiness. CDP still verifies the Profile actually used by the browser. Screenshots report the current virtual-desktop origin, size, and scaling information; negative monitor coordinates are valid.

Claude Code must actually connect to the currently logged-in user's desktop. Prefer normal permission prompts and inspect the specific operation being requested. Do not enable a blanket bypass of permission checks merely to reduce prompts. This plugin is not a system permission manager.[3]

Do not lower PowerShell execution policy just to run the scripts. If `.ps1` is blocked, use the native-Python path described above, or first understand and handle the trust state of downloaded scripts using normal system procedures.

## 5. Tabs and web-page operations

When the browser has multiple pages, run `tabs` first to obtain real target IDs and pass `--target-id` to later operations. Replace `TARGET` in the examples with the actual ID.

```text
webmind cdp --no-auto-launch new-tab --url https://example.com --json
webmind cdp --no-auto-launch switch-tab --target-id TARGET --json
webmind cdp --no-auto-launch close-tab --target-id TARGET --json
webmind cdp --no-auto-launch eval --target-id TARGET --expression "document.title" --json
webmind cdp --no-auto-launch wait-for-selector --target-id TARGET --selector "main" --visible --timeout 10 --json
```

`new-tab` creates a tab; `switch-tab` activates an existing tab and requests that it be brought forward without creating or closing anything; `close-tab` closes only the specified tab and refuses to close the last page tab to avoid shutting down the whole browser. The operating system can still restrict focus stealing, so verify actual window focus before global keyboard input.

`--no-auto-launch` is appropriate for reusing an already connected and verified browser. If the connection is lost, it fails instead of silently opening a new window. Before sending, deleting, publishing, uploading, or performing another externally consequential action, verify the user-authorized target and content. Do not treat a timeout as proof that an action did not occur and resubmit blindly.

### Non-sensitive Unicode and complex text

Prefer CDP `fill` / `insert-text`; desktop `typing type` supports printable ASCII only and does not drive a Chinese IME. `fill` sets a field and dispatches input events, while `insert-text` uses the browser input interface. Complex sites still require verification of the actual result.

The Claude Code edition keeps component input methods such as `--text-stdin` / `--url-stdin` and **does not provide an `--input-file` option**. Do not pass an unimplemented option to this edition. To avoid shell quoting or pipe encoding changing non-sensitive Unicode text, use native Python to send UTF-8 bytes from a verified non-sensitive file to the verified component command.

```python
from pathlib import Path
import subprocess
import sys

root = Path(r"D:\Tools\windows-claudecode")
text_file = Path(r"D:\WebMindData\body.txt")
text = text_file.read_text(encoding="utf-8-sig")
subprocess.run(
    [sys.executable, str(root / "scripts" / "webmind.py"),
     "cdp", "--no-auto-launch", "fill", "--target-id", "TARGET",
     "--selector", "textarea", "--text-stdin", "--json"],
    input=text.encode("utf-8"), check=True,
)
```

This example sends only a non-sensitive test file to an already initialized dedicated browser. The target ID, selector, and paths must match the real page. Do not use this method for sensitive authentication data.

These methods are for non-sensitive content only. Passwords, verification codes, tokens, payment data, and similar secrets must not be placed in arguments, input files, logs, or the clipboard; enter them yourself on the target page. File reading and screenshots do not substitute for authorization to inspect content.

## 6. Two usage modes

### 6.1 Recommended: Mem-bound dedicated CDP browser

This mode uses an installed browser with an independent, persistent Profile inside the selected Mem instead of your everyday default Profile. It is suitable for repeated web tasks, DOM inspection, and reducing coordinate-based interaction and screenshots.

```text
Please use the webmind-claudecode skills and complete the task through the dedicated CDP browser. Read the selected Mem before starting, verify the result, and reconcile only validated reusable knowledge afterward. Without my explicit authorization, do not send, delete, upload, or publish anything. Task: ...
```

The first visit to a site that requires sign-in may require manual login. If the site does not invalidate the session and the Profile is not cleared, later runs can usually reuse that session, but permanent sign-in is not guaranteed. Do not copy an actively used everyday Profile directly into the automation browser.

### 6.2 Explicit alternative: operate an already-open everyday browser

This mode mainly uses desktop screenshots, mouse, and keyboard, without attaching the everyday default Profile to CDP. It normally requires more visual confirmation and is more sensitive to layout, focus, and display scaling. The project's first-run risk acceptance and Mem initialization are still required.

```text
Please use the webmind-claudecode skills, but do not use CDP for this task. Operate the everyday browser I already have open. Read relevant Mem first, verify a real screenshot and pointer position before every desktop click, and reconcile reusable knowledge afterward. Task: ...
```

Claude Code may provide other browser integrations. To ensure this project is used, you can explicitly add: "Do not use Claude-in-Chrome and do not switch browser-control tools on your own during the task."

### Claude Code permission modes

`default` keeps normal approval prompts; `acceptEdits` automatically accepts file edits but does not authorize arbitrary shell commands or external actions; `plan` is for analysis and planning; `dontAsk` does not automatically make restricted tools allowed; `bypassPermissions` skips permission prompts, which is higher risk and is not recommended as the everyday default for WebMind. Available modes, policy restrictions, and exact behavior depend on the actual host version and organizational settings.[3]

## 7. Usage recommendations

### Start with low-risk tasks

Good initial tests include "open a public page and read the title," "search public articles and summarize them," or "type test text into an empty editor." Do not begin with payment, deletion, account permissions, or important files.

### Give clear task boundaries

Email example: "Draft an invitation email in Gmail to the specified recipient, save it only as a draft, do not send it, and verify the recipient first."

Public-web example: "Search for public articles on the specified topic, read relevant content, summarize it, and save the result to the directory I specify. Do not sign in or download executable files."

Externally consequential example: "Prepare the submission. Before the final send or publish action, show me the target and content and wait for my confirmation; then perform the action once." The scope of the original authorization always takes precedence, and an existing login session does not expand that scope.

### If the first task is slow, teach the model

Model capability, page complexity, and website changes can all affect the first run. You can explain the relative position of fields and buttons, whether a button previews or immediately submits, which category must be selected first, and which fields can be filled afterward. These instructions should not include passwords, tokens, or other secrets and should not expand the authorized scope.

At the end of a task, the Agent reviews whether any validated reusable knowledge was learned and reconciles it with existing Mem, removing duplicate or obsolete methods. Keeping the Mem and reading it next time may reduce repeated exploration, but does not guarantee every run will be faster. "Saved to memory" is true only after the write actually succeeds.

### If a search engine rejects automated search

A rejected search query does not mean that a known official site cannot be opened directly. You can take over manually and complete a verification step; you can also ask the model to use another search engine in the **same browser and same Profile**, or directly open a known official URL. Do not automatically solve CAPTCHA, clear login data, rebuild the Profile, or switch control tools to evade a denial.

### Keep operations observable and interruptible

Do not switch windows or type at the same time as desktop automation. Keep the PyAutoGUI failsafe enabled. To stop, prefer the host's stop control or move the pointer to a failsafe corner. This mechanism cannot undo external actions that already completed and does not guarantee interruption of every CDP request.

## 8. Common problems

| Symptom | Check first |
| --- | --- |
| Reports that initialization is missing | Run `mem init-status`; follow the risk-acceptance and path-selection flow instead of editing the pointer manually. |
| Profile or port mismatch | Check the current Mem name and `webmind-profile.json`; do not attach to another browser. |
| Cannot connect after launch | Inspect the error, port conflict, Profile lock, and host approval; do not delete the Profile first. |
| Screenshot works but clicks land incorrectly | Check the latest monitor layout, screenshot region, image scale, and actual pointer position. |
| Text goes into the terminal | Stop, re-verify the target application and field focus, and do not blindly continue with Enter. |
| Unicode text is corrupted | Check UTF-8 file/pipe handling and use the appropriate CDP text input path instead of ASCII keyboard typing. |
| Old knowledge seems missing after an update | Locate the original external Mem and reinitialize by selecting it; do not create a replacement and then delete the old folder. |

If an incorrect send, deletion, upload, or other major unintended result has already occurred, stop at a safe point, perform only necessary read-only checks, and report it. Do not automatically refresh, retry, undo, or clean up.

## 9. Updates, uninstalling, and backups

Before upgrading, finish the current task, back up source modifications, and remember the external Mem location. Removing the code does not sign out website sessions; you are responsible for managing the Profile that contains login state. Do not package and share an entire Mem as if it were only ordinary experience documentation, because it also contains browser data.

Any knowledge you do share should be reviewed and sanitized first. Share only genuinely non-sensitive task Markdown; do not include the Profile, location pointer, cookies, cache, screenshots, or temporary input files.

## 10. References

Official information about Claude Code plugins, marketplaces, and permission modes is listed in [Reference Sources](references/SOURCES.md). Real Windows desktops, browser versions, websites, and system permissions change over time; validate first use with a read-only task on a public page.
