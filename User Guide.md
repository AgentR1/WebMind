# WebMind Windows / Codex User Guide

[Chinese version](%E4%BD%BF%E7%94%A8%E6%95%99%E7%A8%8B.md)

This guide applies only to **Codex on Windows**. The code, launchers, dependencies, and documentation included in the repository and GitHub Release archive are self-contained and do not require a separate edition download.

Before first use, read the [Safety Instructions](Safety%20Instructions.md) in the same directory. This project can change web pages, account state, and desktop state. Its safety constraints cannot guarantee that the model will never make a mistake. Installing dependencies, granting system permissions, and accepting the first-use initialization risk are separate actions and do not substitute for one another.

## 1. What the project can do

The project provides six capability groups: CDP browser control, desktop screenshots, mouse control, keyboard input, bounded waits, and external Mem. The recommended sequence is: read relevant Mem -> prefer CDP/DOM -> use desktop tools only when necessary -> verify results -> reconcile reusable experience.

For web buttons, text input, and page-content reading, a screenshot is usually unnecessary: CDP can query the DOM, locate elements by selector, and send browser input events. File pickers, system dialogs, and browser permission bubbles are outside the page DOM and require desktop tools. Before any coordinate-based desktop action, inspect a current real screenshot instead of relying only on historical coordinates.

This project does not include a browser binary, a pre-authenticated Profile, user Mem, a Python virtual environment, or account credentials. It is also not a remote-control service: Codex, native Windows Python, and the target browser must run on the same Windows device with a visible desktop session.

## 2. Installation and loading

### 2.1 Prepare the environment

Prepare local Codex, Python 3.10 or later, and an installed Chrome / Chromium / Edge browser. The first dependency installation requires network access. Clone the full repository or extract the full Release archive; do not copy only one component, and do not move a virtual environment between computers.

You can also send the following instruction to local Codex together with the real absolute path of the extracted directory:

```text
Please inspect and install the WebMind project in this directory. Read the User Guide and Safety Instructions first, confirm the local environment, and then run the appropriate installation steps. Ask for my approval before installing software, changing configuration, or requesting additional permissions. Do not automatically disable sandboxing or change system security policy.
```

### 2.2 Install from GitHub

OpenAI's official [Skills documentation](https://developers.openai.com/codex/skills) explains that personal Skills are loaded from `$HOME/.agents/skills`, and the built-in `$skill-installer` can install a Skill from another GitHub repository. After the repository is published, copy its HTTPS URL and include the URL with the following request in the same Codex message:

```text
$skill-installer Please install webmind-codex from the GitHub repository URL in this message.
```

After the download finishes, install this project's Python runtime dependencies from native PowerShell:

```powershell
& "$HOME\.agents\skills\webmind-codex\scripts\install.ps1"
& "$HOME\.agents\skills\webmind-codex\scripts\webmind.ps1" doctor --json
```

If the Skill does not immediately appear in the list, reopen Codex.

### 2.3 Install manually from source

Open native PowerShell in the full clone or extracted directory and install:

```powershell
$SourceRoot = 'C:\path\to\webmind-codex'
Set-Location $SourceRoot
py -3 --version
& '.\scripts\install.ps1'
& "$HOME\.agents\skills\webmind-codex\scripts\webmind.ps1" doctor --json
```

Replace `C:\path\to\webmind-codex` with the real source path. By default, the full Skill is installed to `~/.agents/skills/webmind-codex`, and runtime dependencies are stored in a private virtual environment under `%LOCALAPPDATA%\WebMindCodex`. Mem is not stored in either location by default. These paths are resolved dynamically for the current user and are not tied to a particular username or drive letter.

If the system blocks PowerShell scripts, use the equivalent native Python entry points instead of lowering the execution policy:

```powershell
py -3 -B '.\scripts\install.py'
py -3 -B "$HOME\.agents\skills\webmind-codex\scripts\bootstrap.py" doctor --json
```

Reopen the local Codex session after installation. Invoke the Skill explicitly with `$webmind-codex` and confirm that the entry appears in the Skill list. The project uses local Skill-directory discovery.[1]

### 2.4 Unified entry point for later commands

The initialization, diagnostic, and browser examples below use `webmind` as a temporary function in the current shell. Set the real path and define it first. You must define it again in a new terminal; the installer does not create a global `webmind` command.

```powershell
$WebMindRoot = "$HOME\.agents\skills\webmind-codex"
function webmind { & "$WebMindRoot\scripts\webmind.ps1" @args }
```

The Agent should resolve the project root from the actually discovered Skill or plugin path and call the full launcher path from that root instead of assuming this temporary function exists.

### 2.5 Optional installation arguments

`scripts/install.py` supports user-level, project-level, and custom-directory installation. Append the following arguments to the installation command for this edition:

```text
--scope project --project <absolute-project-path>
--skills-dir <Skill-parent-directory>
--data-dir <external-Python-runtime-directory>
--add-agent-rules
--dry-run
--skip-deps
```

A project-level install goes under `.agents/skills/webmind-codex` in that project. `--data-dir` selects the directory for the Python runtime environment and related runtime data and stores that choice in installation metadata; it is not a substitute for choosing a Mem location. `--add-agent-rules` writes bounded routing rules only when explicitly requested and keeps a backup; by default the installer does not modify global Codex instructions or configuration.

`--dry-run` only displays the plan. `--skip-deps` only copies source files and does not mean dependencies or GUI permissions are ready. Do not enable multiple same-name installations without confirming which path is actually being used. For a custom runtime directory, `WEBMIND_CODEX_DATA_DIR` has priority; the compatibility variable `WEBMIND_DATA_DIR` can also affect resolution, so verify the actual path reported by `doctor` after setting either variable.

## 3. First initialization: choose external Mem

Installation does not mean initialization is complete. Before the first concrete web or desktop task, the Agent checks initialization state, recommends this guide and the Safety Instructions, explains that residual risk remains, and asks whether you accept the risk and want to continue. **The Agent must not use `--accept-risk` until you explicitly agree.**

Choose a parent directory outside the Skill, plugin, and source directories. It may be Downloads, Desktop, Documents, or a dedicated user-data directory. Do not place active Mem inside this distribution directory. After you choose the parent directory, discovery checks only its direct children and does not recursively scan an entire drive. If reusable Mem folders are found, you choose whether to attach one.

A new Mem name must have the form `xxx-yyy-mem`: `xxx` is 1-8 lowercase English letters, `yyy` is an integer from 1 through 999 with no leading zero, and the `-mem` suffix is mandatory. **Both `xxx` and `yyy` must each be unique among your WebMind Mem folders on the same computer. Do not reuse either part for another Mem.** For example, `work-42-mem` maps to port **1042**, because the port is always `1000 + yyy`.

After you have accepted the risk and selected the parent directory and name, you can initialize manually:

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
    ...browser-managed data...
  <task-category>/
    memory.md
    flow.md
    ui.md
    rules.md
    notes.md
```

For a new Mem, `global.md` is copied from the bundled `basic-rules.md`; when attaching an existing Mem, its existing `global.md` is preserved. The browser directory is exactly `<Mem-name>-Profile` and resides inside its corresponding Mem. `webmind-profile.json` in the Profile records the absolute path, loopback address, and port; CDP must read and validate this metadata before launching or connecting.

Inside the Skill, only the selected Mem location pointer `components/webmind-mem/mem-location.json` is stored. Active Mem and browser sessions are not stored in the Skill. Browser Profile contents are excluded from Mem indexing, search, and summarization.

Remember the Mem name and location. Normal later tasks should not ask again. After a Skill update or reload, if the location pointer is missing, reselect the existing Mem instead of immediately creating a new one and assuming old experience was lost. To switch Mem or the dedicated browser, re-enter initialization before or after a task; do not bypass configuration by temporarily changing `--endpoint` or `--user-data-dir`.

**The uniqueness rule applies to both name components: every WebMind Mem on the same computer should use a distinct `xxx` and a distinct `yyy`.** Reusing `yyy` would also reuse the same debug port. Choose fresh values when creating another dedicated Mem/browser. The program does not resolve conflicts by closing another browser.

## 4. Environment and browser checks

Run these commands in order:

```text
webmind doctor --json
webmind mem init-status --json
webmind mem check --json
webmind cdp self-check --json
```

If the browser has not started yet, a failed `cdp self-check` does not necessarily mean the installation is broken; the command only checks and does not launch a browser. After initialization, you can launch explicitly:

```text
webmind cdp launch --url https://example.com --json
webmind cdp tabs --json
webmind cdp self-check --json
```

Before every command that may open a browser, the Agent should tell you, "This will open the CDP (Agent-dedicated) Chrome," and then continue. This notice is not an additional confirmation step. If the actual browser is Edge or another browser, the Agent should name the real browser.

Pay particular attention to `profile_verified`, the actual Profile, and the target tab. A reachable port, a correct page title, or a successful launch return value alone does not prove that the Agent connected to the intended browser. Initialization state, dependency readiness, system permissions, and browser availability must also be checked separately.

### Windows environment notes

Use native Windows Python and a host that can access the current logged-in user's desktop. Do not use a WSL Python process to control the Windows desktop. Window focus and desktop session must be correct; a command having run does not prove that the browser received a click or keystroke.

This edition launches the dedicated Profile through a Windows browser process and waits up to 10 seconds for CDP by default. CDP still verifies the Profile actually in use. Screenshot metadata reports the current virtual-desktop origin, size, and scale information; monitors with negative coordinates are valid.

Codex may execute commands in a private desktop different from the user's everyday desktop. This edition checks known desktop-isolation cases. `runtime_ready` in `doctor` does not imply `gui_permissions_ready`. If access is blocked, use Codex's normal approval mechanism only for permissions required by the current task. Do not enable global Full Access or bypass an explicit denial.[2]

Do not lower the system execution policy just to run these scripts. If PowerShell blocks a `.ps1`, use the native Python entry points in this guide or understand and handle the downloaded script's trust state through normal system mechanisms.

## 5. Tabs and web operations

Before operating on an existing tab, always run `tabs` to obtain the real ID and explicitly provide `--target-id` to every relevant command. The CLI no longer selects a tab automatically by URL, title, or list order. Replace `TARGET` in the examples with the real ID.

```text
webmind cdp --no-auto-launch new-tab --url https://example.com --json
webmind cdp --no-auto-launch switch-tab --target-id TARGET --json
webmind cdp --no-auto-launch close-tab --target-id TARGET --json
webmind cdp --no-auto-launch eval --target-id TARGET --expression "document.title" --json
webmind cdp --no-auto-launch wait-for-selector --target-id TARGET --selector "main" --visible --timeout 10 --json
```

`new-tab` creates a tab. `switch-tab` activates the specified existing tab and requests that it be brought to the front; it neither creates nor closes a tab. `close-tab` closes only the specified tab and refuses to close the last page tab to avoid terminating the entire browser. The operating system can still restrict focus stealing, so verify actual window focus before global keyboard input.

`--no-auto-launch` is suitable when reusing an already connected and verified browser. If that connection is lost, the command fails instead of silently opening a new window. Before sending, deleting, publishing, uploading, or taking another consequential action, still verify the user-authorized target and content. Never treat a timeout as proof that the action did not happen and blindly submit again.

### Non-sensitive Chinese and other complex text

Prefer CDP `fill` / `insert-text`. Desktop `typing type` supports printable ASCII only and does not operate a Chinese IME. `fill` sets the field and dispatches input events; `insert-text` uses the browser input interface. Complex sites still require verification of the actual result.

The Codex unified launcher supports UTF-8 `--input-file`, including Chinese and multiline content:

```text
webmind cdp --no-auto-launch fill --target-id TARGET --selector "textarea" --input-file <absolute-path-to-non-sensitive-UTF8-file> --json
webmind cdp --no-auto-launch eval --target-id TARGET --input-file <absolute-path-to-UTF8-script> --json
```

`--input-file` is implemented by the unified launcher; do not pass it directly to a component script. Replace example paths and selectors with values verified for the current task.

These methods are only for non-sensitive content. Passwords, verification codes, tokens, payment data, and similar secrets must not be placed in command arguments, input files, logs, or the clipboard. You must enter them yourself on the target page. File reading and screenshots do not replace authorization for the content being handled.

## 6. Two usage modes

### 6.1 Recommended: dedicated Mem-bound CDP browser

This mode uses an already installed browser with an independent, persistent Profile stored inside the Mem rather than the everyday default Profile. It is suitable for repeated web tasks, DOM access, and reducing coordinate-based actions and screenshots.

```text
$webmind-codex Please use the dedicated CDP browser for this task. Read the selected Mem before starting, verify the result, and then reconcile verified reusable experience. Unless I explicitly authorize it, do not send, delete, upload, or publish anything. The task is...
```

The first visit to a site that requires authentication may require you to log in manually. If the site does not invalidate the session and the Profile is not cleared, later runs can usually reuse the login state, but permanent login reuse is not guaranteed. Do not copy an actively used everyday Profile directly into the automation browser.

### 6.2 Explicit alternative: operate the everyday browser already open

This mode primarily uses desktop screenshots, mouse, and keyboard rather than attaching CDP to the everyday default Profile. It usually needs more visual verification and is more sensitive to layout, focus, and display scaling. First-use risk acceptance and Mem initialization are still required.

```text
$webmind-codex Do not use CDP for this task. Operate the everyday browser I already have open. Read relevant Mem first, confirm the real screenshot and mouse position before each desktop click, and reconcile reusable experience when finished. The task is...
```

Do not expand Codex workspace or host permissions merely because CDP can already reach a website. For consequential actions such as sending, deleting, publishing, or uploading, the task target and authorization scope remain defined by the user.

## 7. Usage recommendations

### Start with low-risk tasks

Good first tests include opening a public page and reading its title, searching for a public article and summarizing it, or typing test text into a blank editor. Do not make the first test a payment, deletion, account-permission change, or operation on an important file.

### Give clear task boundaries

Email example: "Draft an invitation email in Gmail for the specified recipient. Save it as a draft only; do not send it. Verify the recipient first."

Public-web example: "Search for public articles on the specified topic, read the relevant content, summarize it, and save the summary to the directory I specify. Do not sign in or download executable files."

Consequential example: "Prepare the submission. Before the final send or publish action, show me the target and content and wait for my confirmation, then perform the action once." The scope of the original task authorization always takes priority; an existing login session does not authorize broader actions.

### If the first task is slow, you can teach the model

Model capability, page complexity, and website changes can all make a first run slower. You can explain the relative location of an input and button, whether a button previews or submits immediately, which category must be selected first, and which field can be filled afterward. Such guidance must not contain passwords, tokens, or other secrets and must not broaden the authorized scope.

At task end, the Agent reviews whether any verified reusable experience was learned and merges it with existing Mem, removing duplicated or obsolete methods. Keeping the Mem and reading it next time can reduce repeated exploration, but it does not guarantee every run will be faster. "Saved to memory" is only true after the write actually succeeds.

### If a search engine refuses automated search

A rejected search query does not mean a known official website cannot be opened directly. You can manually take over and complete the verification. You can also ask the model to use another search engine in the **same browser and same Profile**, or open the known official site directly. Do not automatically defeat CAPTCHA, clear login data, rebuild the Profile, or switch control tools without authorization.

### Keep operation observable and interruptible

While desktop automation is active, avoid switching windows or typing at the same time. Keep the PyAutoGUI failsafe enabled. To stop, prefer the host's stop control or move the mouse to a failsafe corner. This mechanism cannot undo an external action that already completed and does not guarantee cancellation of every CDP request.

## 8. Common failures

| Symptom | Check first |
| --- | --- |
| Reports that initialization is missing | Run `mem init-status`; follow the risk-acceptance and location-selection flow instead of manually editing the pointer. |
| Profile or port mismatch | Check the current Mem name and `webmind-profile.json`; do not take over another browser. |
| Cannot connect after launch | Inspect the error, port conflicts, Profile lock, and host approval state; do not delete the Profile first. |
| Screenshot succeeds but click is offset | Verify the current monitor layout, screenshot region, image scale, and real mouse position. |
| Input goes to the terminal | Stop first, then re-verify the target application and input focus; do not blindly continue with Enter. |
| Chinese text is garbled | Verify UTF-8 files/pipes; use the corresponding CDP text path instead of ASCII keyboard simulation. |
| Old experience is missing after an update | Recover the original external Mem and reselect it through initialization; do not create a replacement and then delete the old directory. |

If an incorrect send, deletion, upload, or another major unintended result may already have occurred, stop in a safe state, perform only the necessary read-only checks, and report what happened. Do not automatically refresh, retry, undo, or clean up.

## 9. Updates, uninstall, and backup

Before upgrading, end the current task, back up source modifications, and remember the external Mem location. Removing the code does not log out website sessions; a Profile containing login state remains your responsibility. Do not package and share the entire Mem as if it were ordinary experience documentation because it also contains browser data.

Before sharing reusable experience, review and sanitize it. Share only genuinely non-sensitive task Markdown; do not include the Profile, location pointer, cookies, cache, screenshots, or temporary input files.

## 10. Validation scope and references

The GitHub repository does not include internal test suites, internal test reports, or live local-machine data. After installation, run at least `doctor --json`, `mem init-status --json`, and each component's `self-check --json`, then begin with low-risk tasks that do not involve login, payment, publishing, or deletion. Real Windows desktop permissions, focus, display scaling, and browser behavior must be verified on the target computer; static checks cannot replace that acceptance testing. For official host references, see [Sources](references/SOURCES.md).
