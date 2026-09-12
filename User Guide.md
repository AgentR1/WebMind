# WebMind macOS / Claude Code User Guide

中文：[使用教程](使用教程.md)

This guide applies only to **Claude Code on macOS**. The code, launchers, dependencies, and documentation in this repository are self-contained; you do not need to download another edition of the project.

Before first use, read the [Safety Instructions](Safety%20Instructions.md) in the same directory. This project can change web pages, account state, and desktop state. Safety constraints cannot guarantee that the model will never make an incorrect action. Installing dependencies, granting system permissions, and accepting first-run initialization risk are separate actions and do not substitute for one another.

## 1. What the project can do

The project provides six capability groups: CDP browser control, desktop screenshots, mouse control, keyboard input, bounded waiting, and external Mem. The recommended workflow is: read relevant Mem -> prefer CDP/DOM -> use desktop tools only when necessary -> verify the result -> reconcile reusable experience.

Locating web buttons, entering text, and reading page content usually do not require a screenshot first. CDP can query the DOM, locate elements with selectors, and send browser input events. File pickers, system dialogs, browser permission bubbles, and similar UI are outside the page DOM and require desktop tools. Any coordinate-based desktop action must be based on a current real screenshot rather than historical coordinates alone.

This package does not include a browser binary, a signed-in Profile, user Mem, a Python virtual environment, or account credentials. It is not a remote-control service. Claude Code, native Python, and the target browser must run on the same macOS device with a visible desktop session.

## 2. Installation and loading

### 2.1 Prepare the environment

Prepare the latest Claude Code available on the Mac, Python 3.10 or later, Git if you use a clone workflow, and an installed Chrome / Chromium / Edge browser. Internet access is required the first time Python dependencies are installed. Clone the complete repository or fully extract the Release source archive. Do not copy only one component, and do not move a virtual environment between machines.

You can also send the following instruction to Claude Code on the Mac and provide the real absolute path of the extracted directory:

```text
Please inspect and install the WebMind project in this directory. Read the User Guide and Safety Instructions first, verify the local environment, and then perform the appropriate installation steps. Ask for my approval before installing software, changing configuration, or requesting additional permissions. Do not automatically disable sandboxing or change system security policies.
```

### 2.2 Install dependencies from source

When cloning from GitHub, replace `OWNER` with the actual GitHub user or organization:

```bash
git clone https://github.com/OWNER/mac-claudecode.git "$HOME/Tools/mac-claudecode"
WEBMIND_ROOT="$HOME/Tools/mac-claudecode"
python3 --version
bash "$WEBMIND_ROOT/scripts/install.sh"
bash "$WEBMIND_ROOT/scripts/webmind.sh" doctor --json
claude --plugin-dir "$WEBMIND_ROOT"
```

You may instead download the source archive from GitHub Releases. Extract it completely, set `WEBMIND_ROOT` to the real absolute path, and continue from `python3 --version`. The installer first checks the operating system and Python version, then creates a virtual environment at `~/Library/Application Support/WebMind/.venv` and installs dependencies. It does not automatically modify Claude Code configuration. The last command loads the whole directory through the local plugin entry point.[1]

`--plugin-dir` must point to the root that contains `.claude-plugin`, `scripts`, and `skills`. It applies only to the current Claude Code session. Moving or deleting that directory affects later loading. Do not copy only one component.[1]

### 2.3 Unified command entry point

The initialization, diagnostic, and browser examples below use `webmind` as a temporary function in the current terminal. Set the real path and define it first. You must redefine it in a new terminal. The installer does not install a separate global `webmind` executable.

```bash
WEBMIND_ROOT="$HOME/Tools/mac-claudecode"
webmind() { bash "$WEBMIND_ROOT/scripts/webmind.sh" "$@"; }
```

An Agent should locate the project root from the actual discovered Skill or plugin path and call the complete launcher path in that root instead of assuming that this temporary shell function exists.

### 2.4 Persistent plugin installation

After dependency installation in 2.2, you can install the plugin persistently through the GitHub marketplace. Replace `OWNER` with the actual GitHub user or organization:

```text
claude plugin marketplace add OWNER/mac-claudecode
claude plugin install webmind-claudecode@webmind-claudecode
```

When installing from a Release source archive or validating locally before publication, you can replace `OWNER/mac-claudecode` in the first command with the complete plugin-root path. Quote paths that contain spaces. Marketplace installation copies the plugin into the Claude Code cache; after installation, locate the runtime root from the actual Skill path rather than assuming the original source directory remains the runtime directory. Do not enable the same plugin from multiple sources at the same time.[2]

This edition still uses `WEBMIND_DATA_DIR` to customize the Python runtime environment directory. Make sure later runs use the same setting. It does not select the active Mem. First-use initialization is performed by the Agent according to `skills/webmind-mem/SKILL.md` in the installed plugin. You can explicitly invoke `/webmind-claudecode:webmind-mem`.

## 3. First initialization: choose an external Mem

Installation does not mean initialization is complete. Before the first real browser or desktop task, the Agent checks initialization state, recommends this guide and the Safety Instructions, explains that residual risk remains, and asks whether you accept the risk and want to continue. **The Agent must not use `--accept-risk` until you explicitly agree.**

Choose a parent directory outside every Skill, plugin, and source directory. It may be Downloads, Desktop, Documents, or a dedicated user-data folder. Do not place the active Mem inside this distribution. After you choose the parent, only its direct children are inspected; the Agent must not recursively scan the whole disk. If reusable Mem candidates are found, you choose whether to reuse one.

A new Mem name must use the format `xxx-yyy-mem`: `xxx` is 1-8 lowercase English letters, `yyy` is an integer from 1 to 999 with no leading zero, and the `-mem` suffix is mandatory. For example, `work-42-mem` uses port **1042**, because the port is always `1000 + yyy`.

**During initialization, the user must be explicitly told that both `xxx` and `yyy` must each be unique among different Mems on the same computer.** `xxx` is the identifiable Mem prefix and `yyy` determines the dedicated browser port. Before creating a new Mem, inspect existing Mem names and avoid reusing either an existing `xxx` or an existing `yyy`.

After risk acceptance and after selecting the parent directory and Mem name, the same steps can be run manually:

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
  some-task/
    memory.md
    flow.md
    ui.md
    rules.md
    notes.md
```

For a new Mem, `global.md` is copied from the bundled `basic-rules.md`. When attaching an existing Mem, the existing `global.md` is preserved. The browser directory is exactly `<Mem-name>-Profile` and is located directly inside that Mem. `webmind-profile.json` inside the Profile records the absolute path, loopback address, and port. CDP must read and verify this metadata before launching or connecting.

The Skill stores only the selected Mem-location pointer at `skills/webmind-mem/mem-location.json`. It does not store active Mem contents or browser-session data inside the Skill. Browser Profile files are excluded from Mem indexing, search, and summarization.

Remember the Mem name and location. Normal later tasks should not repeatedly ask for them. After updating or reloading the plugin, if the location pointer is missing, select the existing Mem again rather than creating a new one and assuming the old experience was lost. To switch Mem or dedicated browser, re-enter initialization before or after a task. Do not bypass the configured selection by changing `--endpoint` or `--user-data-dir` during a task.

**On the same computer, both `xxx` and `yyy` must remain unique across different Mems.** Reusing `yyy` directly reuses the same CDP port. When initializing a new Mem, inspect existing names and choose an unused `xxx` and an unused `yyy`. The program will not close another browser to resolve a conflict.

## 4. Environment and browser checks

Run:

```text
webmind doctor --json
webmind mem init-status --json
webmind mem check --json
webmind cdp self-check --json
```

If the browser has not been launched yet, a failing `cdp self-check` does not necessarily mean installation is broken. That command only checks; it does not open the browser. After initialization, you can launch explicitly:

```text
webmind cdp launch --url https://example.com --json
webmind cdp tabs --json
webmind cdp self-check --json
```

Before every command that may open a browser, the Agent should tell you that this run opens the CDP (Agent-dedicated) Chrome, then continue. That notice is not an additional confirmation step. If the actual browser is Edge or another supported browser, the Agent should use the real browser name.

Check `profile_verified`, the actual Profile, and the target tab. A reachable port, a correct page title, or a successful launch command alone does not prove that the correct browser is connected. Initialization state, dependencies, system permissions, and browser availability must be checked separately.

### macOS environment notes

This edition uses the corrected LaunchServices launch path. CDP automatically calls the bundled `launch_chrome_macos.sh`, which opens the dedicated browser through `open -na <Browser.app> --args ...` instead of launching the Chrome main process as a short-lived child process. Users do not need to call this helper directly.

Browsers are searched in `/Applications` and `~/Applications` by default. A custom browser path can be supplied with `--chrome-path "/Applications/Google Chrome.app"`; this global option comes before the CDP subcommand. Readiness waits for up to 60 seconds by default. A successful `open` call does not mean CDP is ready. On failure, inspect the error and private launch-request log location. Do not treat that file as a full browser log, and do not forward unreviewed log contents.

Desktop screenshots require the Terminal, IDE, or host application that actually executes the command to have Screen Recording permission. Mouse and keyboard control usually require Accessibility permission. Grant only permissions that are actually necessary through System Settings, and restart the host if macOS requires it. Host approval for shell/CDP access and macOS privacy permissions are separate layers; do not let the Agent modify either layer automatically.

Apple Silicon and Intel systems must use native Python for their architecture and must not copy `.venv` directories between architectures. Retina screenshots use image pixels, while mouse coordinates use logical points. Convert with `x = region.left + image_x / image.scale_x`, and similarly for y. On mixed-scale multi-display setups, prefer screenshots limited to a single display.

Claude Code tool approvals, macOS privacy permissions, and browser sessions are separate layers. Prefer normal approval behavior and grant specific permissions only when needed. Do not treat permission to load the plugin as permission to send, delete, or publish.[3]

## 5. Tabs and web-page operations

When multiple pages are open, run `tabs` first, obtain the real ID, and specify `--target-id` for later actions. Replace `TARGET` in these examples with the actual ID.

```text
webmind cdp --no-auto-launch new-tab --url https://example.com --json
webmind cdp --no-auto-launch switch-tab --target-id TARGET --json
webmind cdp --no-auto-launch close-tab --target-id TARGET --json
webmind cdp --no-auto-launch eval --target-id TARGET --expression "document.title" --json
webmind cdp --no-auto-launch wait-for-selector --target-id TARGET --selector "main" --visible --timeout 10 --json
```

`new-tab` creates a new tab. `switch-tab` activates an existing tab and requests that it be brought forward; it neither creates nor closes a tab. `close-tab` closes only the specified tab and refuses to close the final page tab, avoiding closure of the entire browser. The operating system may still restrict focus changes, so verify the actual focused window before global keyboard input.

`--no-auto-launch` is useful for reusing an already connected and verified browser. If the connection is lost, it fails rather than silently opening a new browser. Before sending, deleting, publishing, uploading, or another consequential action, verify that the user has authorized the exact target and content. Do not assume a timeout means the action did not happen and submit it again without checking state.

### Non-sensitive Chinese and complex text

Prefer CDP `fill` / `insert-text`. Desktop `typing type` only supports printable ASCII and is not a Chinese-IME automation mechanism. `fill` sets a field and dispatches input events; `insert-text` inserts text through the browser input interface. Complex pages still require result verification.

The Claude Code edition supports component stdin inputs such as `--text-stdin` / `--url-stdin`. **There is no `--input-file` option.** Do not pass unimplemented parameters. To avoid shell quoting or pipe encoding changing Chinese text, use native Python to send the bytes of a non-sensitive UTF-8 file to a verified component command.

```python
from pathlib import Path
import subprocess
import sys

root = Path(r"/Users/example/Tools/mac-claudecode")
text_file = Path(r"/Users/example/WebMindData/body.txt")
text = text_file.read_text(encoding="utf-8-sig")
subprocess.run(
    [sys.executable, str(root / "scripts" / "webmind.py"),
     "cdp", "--no-auto-launch", "fill", "--target-id", "TARGET",
     "--selector", "textarea", "--text-stdin", "--json"],
    input=text.encode("utf-8"), check=True,
)
```

This example sends a non-sensitive test file only to an already initialized dedicated browser. Replace the target ID, selector, and paths with values for the actual page. Sensitive authentication data must not be handled this way.

These methods are only for non-sensitive content. Passwords, verification codes, tokens, payment details, and similar data must not be placed in arguments, input files, logs, or the clipboard. Enter them yourself on the target page. File reading and screenshots do not substitute for authorization to use content.

## 6. Two usage modes

### 6.1 Recommended: dedicated CDP browser bound to Mem

This mode uses a browser installed on the computer but a separate persistent Profile stored inside the selected Mem rather than the everyday default Profile. It is suitable for repeated web tasks, DOM reading, and reducing coordinate-based actions and screenshots.

```text
Please use the webmind-claudecode skills and complete the task through the dedicated CDP browser. Read the selected Mem before starting, verify the result, and then reconcile verified reusable experience. Without my explicit authorization, do not send, delete, upload, or publish. The task is...
```

The first visit to a site that requires sign-in may require you to log in manually. If the website has not invalidated the session and the Profile has not been cleared, the signed-in state can often be reused later, but permanent sign-in is not guaranteed. Do not directly copy a running everyday Profile into the automation browser.

### 6.2 Explicit alternative: operate the everyday browser you already opened

This mode mainly uses desktop screenshots, mouse, and keyboard, and does not connect the everyday default Profile to CDP. It usually requires more visual verification and is more sensitive to layout, focus, and display scaling. The project's first-use risk confirmation and Mem initialization are still required.

```text
Please use the webmind-claudecode skills, but do not use CDP for this task. Directly operate the everyday browser I already opened. Read the relevant Mem first, confirm a current screenshot and mouse position before every desktop click, and reconcile reusable experience at the end. The task is...
```

Claude Code may have other browser integrations. If you need to ensure this project is used, add: "Do not use Claude-in-Chrome and do not switch browser-control tools during the task without my permission."

### Claude Code permission modes

`default` keeps normal approvals. `acceptEdits` automatically accepts file edits but does not authorize arbitrary shell commands or external actions. `plan` is for analysis and planning. `dontAsk` does not turn a restricted tool into an allowed tool. `bypassPermissions` skips permission prompts and is higher risk; it is not recommended as the default mode for everyday WebMind use. Available modes, policy limits, and behavior depend on the actual host version and organization settings.[3]

## 7. Usage recommendations

### Start with low-risk tasks

Good first tests include "open a public page and read its title," "search for public articles and summarize them," or "type test text into a blank editor." Do not make the first task a payment, deletion, account-permission change, or operation on important files.

### Give clear task boundaries

Email example: "In Gmail, draft an invitation email to the specified recipient and save it as a draft only; do not send it. Verify the recipient first."

Public-web example: "Search for public articles on the specified topic, read relevant content, summarize it, and save the result to the directory I specify. Do not sign in and do not download executable files."

External-impact example: "Prepare the content for submission. Before the final send or publish action, show me the target and content and wait for my confirmation, then execute it once." The authorization scope of the original task always takes priority. An existing signed-in session does not expand authorization.

### If the first task is slow, you can teach the model

Model capability, page complexity, and website changes can all affect the first run. You may explain the relative position of an input and button, whether a button previews or submits immediately, which category must be selected first, or which field is available only afterward. These instructions must not contain passwords, tokens, or other secrets and must not expand the authorized scope.

After the task, the Agent reviews whether it learned verified reusable experience and reconciles it with old Mem, removing duplicate or obsolete methods. Keeping Mem and reading it next time may reduce repeated exploration, but does not guarantee faster execution every time. A claim that memory was written is valid only after the write actually succeeds.

### If a search engine rejects automated search

A rejected search query does not mean a known official website cannot be opened directly. You can take over and complete verification manually. You may also ask the model to use another search engine within the **same browser and same Profile**, or to open a known official site directly. Do not automatically defeat CAPTCHA, clear login data, rebuild the Profile, or switch control tools just because search was blocked.

### Keep operations observable and interruptible

During desktop operations, do not simultaneously switch windows or type. Keep the PyAutoGUI failsafe enabled. To stop, prefer the host stop control or move the pointer to a failsafe corner. That mechanism does not undo external actions that already completed and does not guarantee cancellation of all CDP requests.

## 8. Common problems

| Symptom | Check first |
| --- | --- |
| Not initialized | Run `mem init-status`; follow the risk-acceptance and path-selection initialization flow instead of editing the pointer manually. |
| Profile or port mismatch | Check the current Mem name and `webmind-profile.json`; do not take over another browser. |
| Cannot connect after launch | Check the error, port conflict, Profile lock, and host approvals; do not delete the Profile first. |
| Screenshot succeeds but click position is wrong | Verify the latest display layout, screenshot region, image scale, and actual mouse position. |
| Input goes into the terminal | Stop first, re-verify the target application and field focus, and do not blindly continue with Enter. |
| Chinese text is garbled | Verify UTF-8 file/pipe handling and use the appropriate CDP text input instead of simulated ASCII keyboard input. |
| Old experience appears missing after update | Find the original external Mem and select it again through initialization; do not create a replacement and then delete the old directory. |

If an incorrect send, delete, upload, or another major unintended result has already occurred, stop at the nearest safe point, perform only necessary read-only checks, and report the situation. Do not automatically refresh, retry, undo, or clean up.

## 9. Updating, uninstalling, and backup

Before upgrading, finish the current task, back up source modifications, and remember the external Mem location. Removing the code does not sign out website sessions. A Profile containing login state remains your responsibility. Do not share an entire Mem as if it were an ordinary experience-document bundle, because it also contains browser data.

Even experience that is safe to share should be reviewed and sanitized first. Share only genuinely non-sensitive task Markdown. Do not include the Profile, location pointer, cookies, caches, screenshots, or temporary input files.

## 10. Validation and references

The GitHub workflow checks Python and Shell syntax, JSON metadata, dependency installation, and the `doctor` result on macOS, but it cannot replace validation of permissions, focus, display scaling, and browser Profile behavior on a real desktop. Start first use with a low-risk public page and verify system permissions and actual outcomes step by step. Claude Code host references are listed in [Reference Sources](references/SOURCES.md).
