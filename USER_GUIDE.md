# WebMind for Claude Code on Windows — User Guide

[中文版](使用教程.md)

This guide covers **WebMind for Claude Code on Windows**. It starts with the simplest installation and first-use path, then provides commands for diagnosis and troubleshooting.

WebMind can change websites, accounts, and the local desktop. Read the [Safety Instructions](SAFETY_INSTRUCTIONS.md) in full before starting. Installing software, granting system access, accepting first-use risk, and authorizing a particular action are separate decisions.

## 1. What WebMind does

WebMind gives Claude Code six local capabilities:

- **CDP and DOM browser control** for reading pages, locating elements, entering text, and managing tabs.
- **Screenshots** for interfaces the DOM cannot describe.
- **Mouse control** for native dialogs and visual-only surfaces.
- **Keyboard control** for a window whose focus has been verified.
- **Bounded waits** for state changes without waiting forever.
- **External Mem** for verified reusable guidance and the dedicated browser profile.

Web tasks normally prefer CDP and DOM because they are more reliable than guessed screenshot coordinates. Desktop tools are fallbacks for file pickers, system dialogs, browser permission prompts, and other surfaces outside page DOM.

WebMind includes no browser, credentials, active Mem, signed-in profile, or Python virtual environment. It is not a remote-control service: Claude Code, Python, and the browser must run on the same Windows computer in a visible desktop session.

## 2. How to install WebMind and its dependencies

**Recommended default: the installer copies the complete plugin into Claude's personal skills directory, `%USERPROFILE%\.claude\skills\webmind-claudecode`. The desktop is only the download source; no separate permanent folder needs to be chosen.** This supported plugin layout is separate from the plugin cache. Marketplace registration remains an optional compatibility or team-distribution route.

Prepare a native Windows 10/11 desktop, Claude Code, native Python 3.10+, Chrome/Chromium/Edge and network access for initial dependencies. Use a current Claude release and verify actual loading in a new session. Keep the complete distribution, including manifests, launchers, all six skills, requirements and user/safety documentation. Do not copy a virtual environment from another computer.

### 2.0 Simplest installation method (recommended)

1. Download and extract the complete distribution to the desktop or another convenient temporary location.
2. In local Claude Code, replace the placeholder with the complete download's real absolute path and send:

   ```text
   Read and follow the Safety Instructions, User Guide, and installation workflow in <absolute path to the complete download>. Run the default installer to copy the complete WebMind plugin with all six Skills into Claude's personal skills directory and install Python dependencies. Run doctor --json from the installed copy and report the plugin path, runtime path, and results. Explain before changing Claude configuration or requesting additional access. Install only in this conversation; restart Claude Code and verify loading in a new conversation before initializing Mem.
   ```

   The Agent should follow [the complete installation workflow](references/INSTALLATION.md) and run the default installer. It copies the whole plugin and prepares dependencies without asking you to choose a permanent source. The equivalent command is:

   ```powershell
   $WebMindDownload = "<absolute path to the complete download>"
   & "$WebMindDownload\scripts\install.ps1"
   ```

3. The reported destination must be Claude's personal skills directory. Dependencies default to `%LOCALAPPDATA%\WebMind\.venv`. Run `doctor --json` from the destination and inspect all six skills and dependencies. Check for an old marketplace or inline WebMind that can shadow the new copy. Unknown targets are not overwritten; marked same-platform updates retain a backup and the destination Mem pointer.
4. **Restart Claude Code and initialize in a NEW conversation.** Confirm the host loads all six skills, invoke `/webmind-claudecode:webmind-mem`, and compare the actual loaded Skill root and that copy's `doctor.plugin_root` with the destination. After verification, you may remove the desktop download yourself. The installer never deletes it.

If `CLAUDE_CONFIG_DIR` is set, the destination is `skills/webmind-claudecode` under that root. Installation and later sessions must use the same setting. `WEBMIND_DATA_DIR` changes dependencies only, must stay outside the plugin and does not choose Mem.

Flags: `--dry-run` validates and prints a plan without changes; `--skip-deps` copies files only; `--deps-only` prepares dependencies for the existing copy without copying it. A file copy or passing doctor does not prove host loading. Installation, loading, Mem risk acceptance and authorization for a specific web action remain separate steps.

### 2.1 Other installation method: temporary local directory

For development or temporary use, set the root to the complete plugin's actual path. The source must remain available while used:

```powershell
$WebMindRoot = "<actual complete plugin path>"
& "$WebMindRoot\scripts\install.ps1" --deps-only
claude --plugin-dir "$WebMindRoot"
```

`--plugin-dir` applies only to that session. Do not enable another same-name copy at the same time. Restart and use a new conversation before Mem initialization.

### 2.2 Other installation method: marketplace compatibility

If the host cannot load plugins from the personal skills directory, update Claude first. If a marketplace is needed, complete the copy in 2.0 and register **the destination**, not the desktop source:

```powershell
$WebMindRoot = Join-Path $(if ($env:CLAUDE_CONFIG_DIR) { $env:CLAUDE_CONFIG_DIR } else { Join-Path $env:USERPROFILE ".claude" }) "skills\webmind-claudecode"
claude plugin marketplace add "$WebMindRoot"
claude plugin install webmind-claudecode@webmind-claudecode --scope user
```

Inspect any existing same-name marketplace before migrating its WebMind origin; preserve unrelated plugins and registrations. A local marketplace with `source: "./"` loads in place. Remote marketplaces normally use a cached copy and must select the edition's correct branch. Never register the desktop download as this workflow's permanent source.

For an already loaded marketplace copy, resolve the root from the actual loaded Skill and run its `scripts\install.ps1 --deps-only`. The default installer creates the personal skills copy and must not be substituted for dependency preparation of a marketplace copy. Verify the actual root and all six skills after restart.

### 2.3 Other installation method: manual Python environment

Check paths, Python and permissions first; do not weaken system execution policy. If the shell wrapper cannot run, invoke the download's `scripts/install.py` directly with native Python 3.10+. To prepare dependencies manually, use `--skip-deps` to copy the plugin first, then create the platform virtual environment `%LOCALAPPDATA%\WebMind\.venv` and install the **destination's** `requirements.txt` with its Python. Run the destination launcher with `doctor --json`. The new session must still verify host loading. The desktop source need not remain once verification passes.

## 3. Initialization

**Do not install and initialize in the same conversation. After installation, restart Claude Code before initializing in a new conversation.**

Before initialization, verify all six skills are discovered by the host, invoke `/webmind-claudecode:webmind-mem` and run doctor from the actual loaded copy. For the default installation, both the loaded Skill root and `doctor.plugin_root` must equal the personal-skills destination, without an old desktop, inline or marketplace copy shadowing it. For an explicitly selected alternative, verify that method's intended root. Stop initialization on loading failures; repair within authorization, restart and verify in a new conversation. Report the actual installed path and keep that copy in place. The desktop download is separate.

After invocation verification, check Python, dependencies, all Skills, the browser, and relevant permissions. Begin formal Mem initialization only when the environment is ready. See the [Mem pre-initialization checks](skills/webmind-mem/SKILL.md#pre-initialization-checks) for the full procedure.

Mem is a user-selected external directory containing verified reusable Markdown guidance and WebMind's dedicated browser profile. The profile may retain sign-in state, so never treat a complete Mem as an ordinary shareable project folder.

### 3.1 Automatic initialization

The first time the agent uses WebMind, it checks initialization. Normal commands are gated until initialization succeeds. The agent should automatically guide the user through:

1. Reading the guide and safety material and understanding residual security and operational risk.
2. Explicitly accepting that risk; the agent must never choose `--accept-risk` for the user.
3. Choosing an external Mem parent; only direct children of that confirmed directory are scanned.
4. Selecting an existing Mem or choosing a new name.
5. Creating or attaching the Mem, Markdown files, dedicated profile, and configuration.
6. Saving the location pointer and reporting the Mem, profile, and loopback port.
7. After success, actively explaining **user's own browser mode, dedicated Agent browser mode, and invisible mode**, including that invisible mode is available only for the dedicated Agent browser. This explanation is required after creating a Mem, attaching an existing one, or reinitializing.

The Agent should explain these choices in its completion response, rather than only
linking to the tutorial:

| Choice | Browser and interaction |
| --- | --- |
| User's own browser mode | Operate your already-open everyday Chrome through screenshots, mouse and keyboard, reusing the current session without attaching its Profile to CDP. |
| Dedicated Agent browser mode | Use the independent Profile inside the selected Mem through CDP/DOM, in invisible mode by default. Choose visible mode for manual sign-in or takeover. |
| Invisible mode | **Only the dedicated Agent browser** runs without a visible window and is operated through CDP/DOM. Pause for a transition to visible mode when manual sign-in or takeover is needed. |

You may choose before each task. **The dedicated Agent browser defaults to invisible
mode without waiting for extra confirmation.** Choose visible mode with `--visible-mode`
for the current task; the choice does not carry over to the next task. Choosing your
own browser means visible everyday Chrome. The dedicated Agent browser remains
invisible unless visible mode is requested. See section 4.2 for commands and transitions, and section
5.1 for example requests.

Mem must remain outside source, plugin, and Skill directories. Its parent must exist and must not link back into them. Choose a stable private user directory, not temporary storage, a public sync folder, or a code repository.

Names have the form `xxx-yyy-mem`: `xxx` is 1–8 lowercase ASCII letters; `yyy` is 1–999 without a leading zero; `-mem` is required. Every new Mem on one computer must use both an `xxx` and a `yyy` that are individually unique.

For example, `work-42-mem` uses `work-42-mem-Profile` and port 9042 (`9000 + 42`). All derived ports are in the range 9001-9999. Syntax validation cannot prove computer-wide uniqueness. Remember the Mem name and location; if an update loses the pointer, reselect the original Mem.

### 3.2 Manual initialization

If automatic initialization fails, ask the agent to try the guided flow again:

```text
Check WebMind initialization again according to the User Guide. First remind me to restart Claude Code after installation and initialize in a new conversation. Verify the Skill invocation, report its actual location and file-storage reminder, then check the environment. Once these checks pass, explain risk and ask for my Mem location and name. Do not accept risk or choose a path or name for me.
```

Use manual commands only if automatic initialization consistently fails:

```powershell
$WebMindRoot = Join-Path $(if ($env:CLAUDE_CONFIG_DIR) { $env:CLAUDE_CONFIG_DIR } else { Join-Path $env:USERPROFILE ".claude" }) "skills\webmind-claudecode"
$MemParent = 'D:\WebMindData'
$MemName = 'work-42-mem'
New-Item -ItemType Directory -Path $MemParent -Force | Out-Null
& "$WebMindRoot\scripts\webmind.ps1" mem init-status --json
& "$WebMindRoot\scripts\webmind.ps1" mem scan --parent $MemParent --json
& "$WebMindRoot\scripts\webmind.ps1" mem name-info --name $MemName --json
& "$WebMindRoot\scripts\webmind.ps1" mem init --mem-path (Join-Path $MemParent $MemName) --accept-risk --json
& "$WebMindRoot\scripts\webmind.ps1" mem check --json
```

Replace the WebMind path, `D:\WebMindData`, and `work-42-mem` with the user's real choices. Run `--accept-risk` only after the user reads the safety material and explicitly agrees. Do not hand-edit `skills/webmind-mem/mem-location.json`, generated ports, or profile paths, and do not force a Mem switch through a normal command.

## 4. Environment and browser feature checks

### 4.0 Simplest environment and browser check

After initialization, send the agent:

```text
Check the complete WebMind skills environment, including Python, dependencies, initialization, and component files. Then use WebMind CDP to open the dedicated agent browser, open any low-risk public page, and verify the real browser profile, CDP connection, and tab. Do not sign in, send, delete, upload, or publish anything. Report every result and anything still unverified.
```

Before any command that may launch a browser, the agent should identify the real browser executable and the Mem-bound dedicated agent profile that will open.

### 4.1 Manual environment and browser check

Replace the WebMind path, then run:

```powershell
$WebMindRoot = Join-Path $(if ($env:CLAUDE_CONFIG_DIR) { $env:CLAUDE_CONFIG_DIR } else { Join-Path $env:USERPROFILE ".claude" }) "skills\webmind-claudecode"
& "$WebMindRoot\scripts\webmind.ps1" doctor --json
& "$WebMindRoot\scripts\webmind.ps1" mem init-status --json
& "$WebMindRoot\scripts\webmind.ps1" mem check --json
& "$WebMindRoot\scripts\webmind.ps1" cdp launch --url https://example.com --json
& "$WebMindRoot\scripts\webmind.ps1" cdp tabs --json
& "$WebMindRoot\scripts\webmind.ps1" cdp self-check --json
```

`doctor` should confirm Python, dependencies, and five executable components; wait is a workflow Skill; initialization should be `true`; `mem check` should report no missing items; browser results should show the correct profile and loopback port; and `tabs` should include `example.com` with a real `target-id`.

`cdp self-check` never launches the browser, so failure while it is stopped does not by itself mean installation is broken. A reachable port, correct URL, or title does not independently prove profile ownership. List tabs first and use the exact current `target-id` for every existing-tab command. After a timeout, inspect state read-only before retrying any consequential action.

Desktop tools require the signed-in user's interactive Windows desktop. Host command approval and desktop reachability are separate conditions. Multi-monitor layouts can include negative coordinates; before clicking, recheck the latest screenshot, region scale, and real pointer position.

### 4.2 Choose invisible mode for each task

Before each task, you may say "use invisible mode" or "do not use invisible mode".
**If omitted, the Agent uses the dedicated browser in invisible mode without waiting for another choice.**
The choice applies only to the current task; do not inherit it from a previous task
or store it as a default Mem preference.

Invisible mode applies only to the dedicated Agent CDP browser. The browser runs
locally without a visible window; CDP/DOM actions and non-sensitive CDP page screenshots
remain available. The user cannot interact with it through the desktop mouse and
keyboard. Direct operation of everyday Chrome does not support this mode.

Example request: "Use invisible mode for this task to read public pages and summarize
the information. The task is: ..."

After initialization, manual commands are:

```powershell
& "$WebMindRoot\scripts\webmind.ps1" cdp --invisible-mode launch --url https://example.com --json
& "$WebMindRoot\scripts\webmind.ps1" cdp --invisible-mode --no-auto-launch tabs --json
& "$WebMindRoot\scripts\webmind.ps1" cdp --invisible-mode self-check --json
```

Mode flags select a new browser's launch mode: omit them or use `--invisible-mode`
for invisible mode, or use `--visible-mode` for visible mode. Put the flag before the
subcommand; the two flags are mutually exclusive. Existing verified browsers retain
their actual mode, even when it differs from the request. Before page actions, the
Agent reads `tabs --json` or `self-check --json`; when `browser_reused` is true, it
relays `browser_mode_notice` once and continues without waiting for confirmation.
The notice says the existing browser's mode will be reused and asks the user to press
ESC to stop the Agent if a mode change is desired. ESC means the host stop control,
not an Escape event sent to the webpage. The output `browser_mode` reports the verified actual mode,
`invisible` or `visible`. `new-tab --background` only controls tab activation; it
does not select the browser mode.

Both modes retain the same Mem, dedicated Profile and port verification. If the running
browser's mode differs, announce its actual mode and continue using it without closing
or restarting it. To switch after the user stops or requests a change,
check unfinished work, then have the user close the dedicated browser or explicitly
authorize the Agent to close it. Confirm that it has exited before relaunching the same
Profile in the selected mode. Never run two instances on one Profile or terminate all
Chrome processes. The invisible process does not exit when a command or task ends;
a later task reuses its actual mode; launch defaults apply only when a new browser is needed.

For manual sign-in, verification codes, MFA, CAPTCHA, payment authentication or a native
dialog requiring visible interaction, pause and explain the transition to visible mode
for user takeover. Restarting may lose unsaved page state; retained sign-in validity
depends on the website. Invisible mode cannot be combined with `launch --new-window`.
Desktop screenshots, OS mouse and keyboard cannot operate the hidden page. Restrictions
on authentication screenshots, secrets and authorization continue to apply.

## 5. Important notes (strongly recommended)

### 5.1 WebMind's three browser choices

Choose user's own browser mode, dedicated Agent browser mode, or invisible mode.
Invisible mode is a way to start the dedicated Agent browser with its independent
Profile; it is not available for everyday Chrome. It is the default for the dedicated
Agent browser; request visible mode explicitly for the current task when needed.

#### Dedicated Agent browser mode (visible)

WebMind starts an installed Chrome, Chromium, or Edge executable with an independent profile inside the selected Mem and a Mem-bound loopback port. The agent uses DOM/CDP for targeting, input, and tab management.

Advantages: stable targeting, Unicode input, explicit page-state checks, and separation from the everyday profile. Disadvantages: sites normally require a separate user-performed sign-in; the local debugging endpoint must remain private and verified; and native dialogs still need desktop tools.

```text
Use WebMind skills and the dedicated agent CDP browser. Read relevant Mem before starting and record only verified reusable experience afterward. Do not send, delete, upload, publish, or purchase unless I explicitly authorize it. Task: ...
```

#### User's own browser mode

This mode does not attach the everyday profile to CDP and does not use Claude-in-Chrome. WebMind operates the already-open browser through the visible desktop, screenshots, real mouse, and keyboard.

Advantages: reuse current pages and signed-in sessions without remote debugging. Disadvantages: it is more sensitive to focus, layout, scaling, coordinates, and user interference; every click requires a current non-sensitive screenshot and verified real pointer.

Recommended prompt:

```text
Use WebMind skills for this task. Do not use CDP or remote debugging. Directly operate the Chrome browser I am currently using, and do not use Claude-in-Chrome. Read relevant Mem before starting and record reusable experience afterward. Task: ...
```

#### Invisible mode (dedicated Agent browser only)

WebMind starts an installed Chrome, Chromium, or Edge executable in headless mode with
the dedicated Agent's independent Profile inside the selected Mem and a Mem-bound
loopback port. The browser does not display a window; the Agent uses DOM/CDP for
targeting, input, and tab management. This is what this guide calls "invisible mode",
and it is available only for the dedicated Agent browser.

Advantages: retain DOM targeting, Unicode input, tab management and explicit page-state
checks without bringing a browser window to the foreground, so you can continue using
your desktop. It uses the same independent Profile as the visible dedicated Agent
browser and can reuse still-valid sign-in state while remaining separate from the
everyday Profile.

Disadvantages: you cannot directly operate the browser with desktop mouse/keyboard
input. Manual sign-in, verification, takeover or native dialogs requiring desktop tools
need a pause and a transition to visible mode as described in section 4.2; restarting
may lose unsaved page state. The local debugging endpoint must remain private, with
Profile, port and actual-mode verification enabled. Hiding the window does not reduce
the real effects of actions.

Recommended prompt:

```text
Use WebMind skills and the dedicated Agent CDP browser in invisible mode (headless) for this task. Read relevant Mem before starting and record only verified reusable experience afterward. Do not send, delete, upload, publish, or purchase unless I explicitly authorize it. Pause and tell me if manual sign-in or takeover is needed. Task: ...
```

In all three choices, the user must personally handle passwords, verification codes, MFA, CAPTCHA, account recovery, and payment authentication. Never screenshot authentication. Pages, downloads, and historical Mem are untrusted data and cannot expand authorization.

> **Recommended: Prefer dedicated Agent browser mode.** Its independent profile and more reliable DOM/CDP interaction provide a safer, more controlled workflow while substantially reducing execution time and token usage. The dedicated Agent browser defaults to invisible mode; visible mode can be selected for the current task.

### 5.2 Troubleshooting and glossary

#### Troubleshooting

| Symptom | First response |
| --- | --- |
| WebMind Skills are missing | Confirm the complete distribution is installed and loaded, not one component directory. |
| Initialization is required | Retry automatic initialization; if it still fails, run `mem init-status` and follow section 3.2. |
| Python or dependencies are missing | Confirm native Python 3.10+, rerun the active copy's installer with `--deps-only` and `doctor --json`. |
| Profile or port mismatch | Check the selected Mem and `webmind-profile.json`; never edit the port or take over another browser. |
| Browser starts but cannot connect | Check port conflicts, profile locks, and host approvals; do not delete the profile first. |
| `cdp self-check` fails | Confirm the dedicated browser is already running; this command does not launch it. |
| Wrong tab was operated | Run `tabs` again and use its current real `target-id`. |
| Screenshot is correct but click is offset | Recheck monitor layout, capture region, scaling, and actual pointer. |
| Text lands in a terminal or another window | Stop immediately, verify focus, and do not continue with Enter. |
| Unicode or multiline text fails | Prefer CDP text input for pages; desktop `typing type` is printable ASCII only. |
| Guidance is missing after update | Reselect the original external Mem instead of creating an arbitrary replacement. |
| Authentication or CAPTCHA blocks progress | Stop automation and let the user take over; do not switch tools to evade it. |

After an unintended send, deletion, upload, purchase, or other major result, stop and perform only necessary read-only checks. Do not refresh, retry, undo, or clean up before the user decides.

#### Glossary

| Term | Meaning |
| --- | --- |
| CDP | Chrome DevTools Protocol, a browser debugging and automation interface. |
| DOM | The structured representation of a web page. |
| Mem | The external persistent directory for reusable guidance and dedicated browser data. |
| Profile | A browser user-data directory that may retain sign-in state. |
| `target-id` | The identifier assigned to one concrete tab by CDP. |
| Loopback address | A network address reachable only from the local computer. |
| Dedicated agent browser | A browser using the Mem profile and verified CDP control. |
| Everyday browser | The user's normal Chrome, operated only through the visible desktop in this mode. |
| Claude-in-Chrome | A separate Claude browser integration, not WebMind's desktop-control mode. |

### 5.3 Updates, removal, and backup

For the default install, run the installer from a new complete download to update. It preserves the destination Mem pointer and backs up the previous plugin under `webmind-install-backups` in the Claude configuration root. Temporary and marketplace copies use `--deps-only` for dependencies. Restart and verify in a new conversation after updating. To remove the default copy, disable `webmind-claudecode@skills-dir` or remove the verified personal-skills folder after ending active tasks. Handle backups separately; they can contain private pointers. External Mem/Profile is never removed with the program.

Before updating, finish active tasks and record the Mem name and absolute path. Update the complete distribution, reinstall dependencies, then run `doctor --json` and `mem init-status --json`. If the pointer is lost, reselect the original Mem. Never mix individual components from different versions.

When upgrading from a release that used the old port rule, close the dedicated agent browser first. Reselect the same Mem through initialization and explicitly accept the initialization risk. WebMind migrates only metadata that exactly matches the legacy rule, upgrading it to schema 2 and the new `9000 + yyy` port. It does not delete the browser profile or rewrite unknown or inconsistent metadata.

For a temporary local plugin, stop using `--plugin-dir`. Remove a marketplace installation through Claude Code plugin management. Remove the runtime `.venv` only after confirming it is no longer needed. None of these actions deletes external Mem or signs out websites automatically.

The safest experience backup contains only reviewed, sanitized Markdown. Never publicly share `*-Profile`, cookies, sign-in data, `mem-location.json`, `webmind-profile.json`, screenshots, logs, or secrets. For private disaster recovery of a full Mem, close the browser first and store the backup as sensitive credentials in encrypted, access-controlled storage.

After installation or update, test with public pages and low-risk data. Static diagnostics cannot validate real desktop permission, focus, scaling, or browser behavior. See [Reference sources](references/SOURCES.md).
