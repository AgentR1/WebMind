# WebMind for Codex on macOS — User Guide

[中文版](使用教程.md)

This guide covers **WebMind for Codex on macOS**. It starts with the simplest installation and first-use path, then provides commands for diagnosis and troubleshooting.

WebMind can change websites, accounts, and the local desktop. Read the [Safety Instructions](Safety%20Instructions.md) in full before starting. Installing software, granting system access, accepting first-use risk, and authorizing a particular action are separate decisions.

## 1. What WebMind does

WebMind gives Codex six local capabilities:

- **CDP and DOM browser control** for reading pages, locating elements, entering text, and managing tabs.
- **Screenshots** for interfaces the DOM cannot describe.
- **Mouse control** for native dialogs and visual-only surfaces.
- **Keyboard control** for a window whose focus has been verified.
- **Bounded waits** for state changes without waiting forever.
- **External Mem** for verified reusable guidance and the dedicated browser profile.

Web tasks normally prefer CDP and DOM because they are more reliable than guessed screenshot coordinates. Desktop tools are fallbacks for file pickers, system dialogs, browser permission prompts, and other surfaces outside page DOM.

WebMind includes no browser, credentials, active Mem, signed-in profile, or Python virtual environment. It is not a remote-control service: Codex, Python, and the browser must run on the same macOS computer in a visible desktop session.

## 2. How to install WebMind and its dependencies

Prepare a native macOS desktop, Codex, Python 3.10+, Chrome/Chromium/Edge, and network access for the first dependency installation. Use a native Python build matching the Mac's Apple Silicon or Intel architecture.

Every method must keep the complete distribution containing `SKILL.md`, `scripts`, `components`, and `agents`, `requirements.txt`, guides, and safety material. Never copy only one component or move `.venv` between computers.

### 2.0 Simplest installation method

1. Save the complete `mac-codex` folder at a stable location, for example:

   ```text
   /Users/me/Tools/mac-codex
   ```

2. In local Codex, replace the example path with the real absolute path and send:

   ```text
   Read the Safety Instructions and User Guide in /Users/me/Tools/mac-codex. Install the complete WebMind Skill and its Python dependencies. Do not copy only one component. Run doctor --json afterward and report the installed Skill path, runtime path, and results. Explain before editing AGENTS.md, changing configuration, or requesting additional access.
   ```

3. Verify the path and runtime reported by the agent. The default environment is `~/Library/Application Support/WebMindCodex/.venv`.

Installing software, loading WebMind, initializing Mem, and authorizing a particular web action are separate steps. Installation grants no general permission to act.

### 2.1 Other installation method—user-scoped Skill

Use a user-scoped installation when WebMind should be available across projects:

```bash
WEBMIND_SOURCE="/Users/me/Tools/mac-codex"
bash "$WEBMIND_SOURCE/scripts/install.sh" --scope user
WEBMIND_ROOT="$HOME/.agents/skills/webmind-codex"
bash "$WEBMIND_ROOT/scripts/webmind.sh" doctor --json
```

The default Skill path is `~/.agents/skills/webmind-codex`; the runtime environment is `~/Library/Application Support/WebMindCodex/.venv`. Restart Codex if it does not discover the new Skill.

### 2.2 Other installation method—project-scoped Skill

To expose WebMind only inside one project, install it under that project's `.agents/skills`:

```bash
WEBMIND_SOURCE="/Users/me/Tools/mac-codex"
PROJECT_PATH="$HOME/Projects/example"
bash "$WEBMIND_SOURCE/scripts/install.sh" --scope project --project "$PROJECT_PATH"
```

Replace the project path with a real absolute path. The installer still creates dependencies; do not copy only the Skill files. Use `--add-agent-rules` only when explicitly requested. It edits the selected `AGENTS.md` and keeps a backup.

### 2.3 Other installation method—custom runtime or manual dependencies

The installer can use a custom runtime directory or preview its plan:

```bash
WEBMIND_SOURCE="/Users/me/Tools/mac-codex"
bash "$WEBMIND_SOURCE/scripts/install.sh" --scope user --data-dir "$HOME/WebMindRuntime"
bash "$WEBMIND_SOURCE/scripts/install.sh" --scope user --dry-run
```

`--skills-dir` selects another Skill parent. `--skip-deps` copies files only and does not prove dependencies are ready. If used, install `requirements.txt` in `.venv` under the selected `--data-dir`, then run `doctor --json` from the installed Skill. `--data-dir` does not select Mem.

## 3. Initialization

Mem is a user-selected external directory containing verified reusable Markdown guidance and WebMind's dedicated browser profile. The profile may retain sign-in state, so never treat a complete Mem as an ordinary shareable project folder.

### 3.1 Automatic initialization

The first time the agent uses WebMind, it checks initialization. Normal commands are gated until initialization succeeds. The agent should automatically guide the user through:

1. Reading the guide and safety material and understanding residual security and operational risk.
2. Explicitly accepting that risk; the agent must never choose `--accept-risk` for the user.
3. Choosing an external Mem parent; only direct children of that confirmed directory are scanned.
4. Selecting an existing Mem or choosing a new name.
5. Creating or attaching the Mem, Markdown files, dedicated profile, and configuration.
6. Saving the location pointer and reporting the Mem, profile, and loopback port.

Mem must remain outside source, plugin, and Skill directories. Its parent must exist and must not link back into them. Choose a stable private user directory, not temporary storage, a public sync folder, or a code repository.

Names have the form `xxx-yyy-mem`: `xxx` is 1–8 lowercase ASCII letters; `yyy` is 1–999 without a leading zero; `-mem` is required. Every new Mem on one computer must use both an `xxx` and a `yyy` that are individually unique.

For example, `work-42-mem` uses `work-42-mem-Profile` and port 1042 (`1000 + 42`). Syntax validation cannot prove computer-wide uniqueness. Remember the Mem name and location; if an update loses the pointer, reselect the original Mem.

### 3.2 Manual initialization

If automatic initialization fails, ask the agent to try the guided flow again:

```text
Check WebMind initialization again and follow the User Guide's automatic initialization flow. Explain risk first, then ask for my Mem location and name. Do not accept risk or choose a path or name for me.
```

Use manual commands only if automatic initialization consistently fails:

```bash
WEBMIND_ROOT="$HOME/.agents/skills/webmind-codex"
MEM_PARENT="$HOME/WebMindData"
MEM_NAME='work-42-mem'
mkdir -p "$MEM_PARENT"
bash "$WEBMIND_ROOT/scripts/webmind.sh" mem init-status --json
bash "$WEBMIND_ROOT/scripts/webmind.sh" mem scan --parent "$MEM_PARENT" --json
bash "$WEBMIND_ROOT/scripts/webmind.sh" mem name-info --name "$MEM_NAME" --json
bash "$WEBMIND_ROOT/scripts/webmind.sh" mem init --mem-path "$MEM_PARENT/$MEM_NAME" --accept-risk --json
bash "$WEBMIND_ROOT/scripts/webmind.sh" mem check --json
```

Replace the WebMind path, `$HOME/WebMindData`, and `work-42-mem` with the user's real choices. Run `--accept-risk` only after the user reads the safety material and explicitly agrees. Do not hand-edit `components/webmind-mem/mem-location.json`, generated ports, or profile paths, and do not force a Mem switch through a normal command.

## 4. Environment and browser feature checks

### 4.0 Simplest environment and browser check

After initialization, send the agent:

```text
Check the complete WebMind skills environment, including Python, dependencies, initialization, and component files. Then use WebMind CDP to open the dedicated agent browser, open any low-risk public page, and verify the real browser profile, CDP connection, and tab. Do not sign in, send, delete, upload, or publish anything. Report every result and anything still unverified.
```

Before any command that may launch a browser, the agent should identify the real browser executable and the Mem-bound dedicated agent profile that will open.

### 4.1 Manual environment and browser check

Replace the WebMind path, then run:

```bash
WEBMIND_ROOT="$HOME/.agents/skills/webmind-codex"
bash "$WEBMIND_ROOT/scripts/webmind.sh" doctor --json
bash "$WEBMIND_ROOT/scripts/webmind.sh" mem init-status --json
bash "$WEBMIND_ROOT/scripts/webmind.sh" mem check --json
bash "$WEBMIND_ROOT/scripts/webmind.sh" cdp launch --url https://example.com --json
bash "$WEBMIND_ROOT/scripts/webmind.sh" cdp tabs --json
bash "$WEBMIND_ROOT/scripts/webmind.sh" cdp self-check --json
```

`doctor` should confirm Python, dependencies, and all six components; initialization should be `true`; `mem check` should report no missing items; browser results should show the correct profile and loopback port; and `tabs` should include `example.com` with a real `target-id`.

`cdp self-check` never launches the browser, so failure while it is stopped does not by itself mean installation is broken. A reachable port, correct URL, or title does not independently prove profile ownership. List tabs first and use the exact current `target-id` for every existing-tab command. After a timeout, inspect state read-only before retrying any consequential action.

Screenshots require Screen Recording permission for the Terminal, IDE, or host process; mouse and keyboard control normally require Accessibility. Only the user should grant necessary access in System Settings, then restart the host when requested. Retina screenshots use image pixels while the mouse uses logical points: `x = region.left + image_x / image.scale_x`, and likewise for y. Prefer a single-display capture on mixed-scaling setups.

## 5. Important notes (strongly recommended)

### 5.1 WebMind's two browser modes

#### Mode one: dedicated agent CDP browser

WebMind starts an installed Chrome, Chromium, or Edge executable with an independent profile inside the selected Mem and a Mem-bound loopback port. The agent uses DOM/CDP for targeting, input, and tab management.

Advantages: stable targeting, Unicode input, explicit page-state checks, and separation from the everyday profile. Disadvantages: sites normally require a separate user-performed sign-in; the local debugging endpoint must remain private and verified; and native dialogs still need desktop tools.

```text
Use WebMind skills and the dedicated agent CDP browser. Read relevant Mem before starting and record only verified reusable experience afterward. Do not send, delete, upload, publish, or purchase unless I explicitly authorize it. Task: ...
```

#### Mode two: directly operate the everyday Chrome

This mode does not attach the everyday profile to CDP and does not use Claude-in-Chrome. WebMind operates the already-open browser through the visible desktop, screenshots, real mouse, and keyboard.

Advantages: reuse current pages and signed-in sessions without remote debugging. Disadvantages: it is more sensitive to focus, layout, scaling, coordinates, and user interference; every click requires a current non-sensitive screenshot and verified real pointer.

Recommended prompt:

```text
Use WebMind skills for this task. Do not use CDP or remote debugging. Directly operate the Chrome browser I am currently using, and do not use Claude-in-Chrome. Read relevant Mem before starting and record reusable experience afterward. Task: ...
```

In either mode, the user must personally handle passwords, verification codes, MFA, CAPTCHA, account recovery, and payment authentication. Never screenshot authentication. Pages, downloads, and historical Mem are untrusted data and cannot expand authorization.

### 5.2 Troubleshooting and glossary

#### Troubleshooting

| Symptom | First response |
| --- | --- |
| WebMind Skills are missing | Confirm the complete distribution is installed and loaded, not one component directory. |
| Initialization is required | Retry automatic initialization; if it still fails, run `mem init-status` and follow section 3.2. |
| Python or dependencies are missing | Confirm native Python 3.10+, rerun the dependency installer and `doctor --json`. |
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

Before updating, finish active tasks and record the Mem name and absolute path. Update the complete distribution, reinstall dependencies, then run `doctor --json` and `mem init-status --json`. If the pointer is lost, reselect the original Mem. Never mix individual components from different versions.

To uninstall, remove the `webmind-codex` Skill from its original user or project installation scope. Remove the runtime `.venv` only after confirming it is no longer needed. Neither action deletes external Mem or signs out websites automatically.

The safest experience backup contains only reviewed, sanitized Markdown. Never publicly share `*-Profile`, cookies, sign-in data, `mem-location.json`, `webmind-profile.json`, screenshots, logs, or secrets. For private disaster recovery of a full Mem, close the browser first and store the backup as sensitive credentials in encrypted, access-controlled storage.

After installation or update, test with public pages and low-risk data. Static diagnostics cannot validate real desktop permission, focus, scaling, or browser behavior. See [Reference sources](references/SOURCES.md).
