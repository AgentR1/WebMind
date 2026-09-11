# Setup and operation

## Requirements

Use local Codex with shell execution on native Windows or macOS. Install Python
3.10+ and Google Chrome, Chromium or Edge on that same computer. A Python version
with wheels for the listed dependencies is preferable; Python 3.11 or 3.12 is a
conservative baseline. This project does not install Codex or a browser and does
not require an OpenAI API key of its own. It uses Codex's existing local session.

The current local-skill discovery layout is documented in the official sources
listed in `SOURCES.md` [1]. The installer uses **real file copies**, not symlinks,
so Windows Developer Mode is not required.

## Windows

Extract the archive, open native PowerShell in `webuse-codex`, then run:

```powershell
& '.\scripts\install.ps1'
& "$HOME\.agents\skills\webuse-codex\scripts\webuse.ps1" doctor --json
```

Install scripts accept Python-style arguments unchanged:

```powershell
& '.\scripts\install.ps1' --scope project --project 'D:\Projects\My project'
& '.\scripts\install.ps1' --data-dir 'D:\WebUseCodex Data' --add-agent-rules
```

If execution policy blocks a local script, do not weaken the system policy. Use
its Python equivalent from the same directory:

```powershell
py -3 -B '.\scripts\install.py'
py -3 -B "$HOME\.agents\skills\webuse-codex\scripts\bootstrap.py" doctor --json
```

A UTF-8 `--input-file` is preferred for Chinese text, JavaScript and multiline
memory updates. The wrapper also sets UTF-8 for legacy PowerShell pipelines, but
a pipeline may add a trailing line ending. Quotes within native argument values
can be altered by Windows PowerShell 5.1; put complex JS/text in a file instead.
The Python launcher option avoids any need to change PowerShell security policy.

Use **native Windows**, not a Linux Python in WSL. Codex's Windows sandbox can
have a private desktop. That desktop cannot see or control your ordinary browser
window. The launcher detects a known non-interactive desktop before GUI actions
and returns a clear error. Use Codex's approval mechanism for an exact host
command, or run that command manually in the signed-in user's terminal. The
package does not change `config.toml`, sandbox settings, ACLs, or firewall rules.
See the official Windows and sandbox documentation [2, 4].

## macOS

Extract the archive, open Terminal in `webuse-codex`, then run:

```bash
bash './scripts/install.sh'
bash "$HOME/.agents/skills/webuse-codex/scripts/webuse.sh" doctor --json
```

Optional project installation / external runtime directory:

```bash
bash './scripts/install.sh' --scope project --project "$HOME/Projects/My project"
bash './scripts/install.sh' --data-dir "$HOME/WebUseCodex Data" --add-agent-rules
```

Give the actual application hosting the Python command (Terminal, iTerm, your IDE,
or Codex's desktop host, as applicable) **Screen Recording** and **Accessibility**
permissions in System Settings > Privacy & Security. Fully restart that host app
after changing permissions. `doctor` checks permissions without prompting, taking
a screenshot or moving the mouse. It never automatically grants permissions.

The installer creates a native Python environment for the interpreter you invoke;
use native arm64 Python on Apple Silicon and x86_64 Python on Intel, and do not
copy a Windows or different-architecture virtual environment between machines.
Retina screenshots include image/desktop scale metadata; the agent must convert
image pixels back to logical mouse coordinates. Mixed-DPI multiple displays still
need a real-machine smoke test and a screenshot region confined to one monitor.

## Discover and invoke

Start a new local Codex session after installation if the skill is not immediately
visible. In the CLI/IDE, use `/skills` or include this in the prompt [1]:

```text
$webuse-codex Help me complete this authorized website task. Use the selected Mem
folder before starting and reconcile reusable experience after verifying success.
```

All six original capabilities are retained, but they are routed through **one
self-contained Codex skill** so installation does not break shared relative paths.
The old individual skill texts are now `components/*/GUIDE.md`, loaded only when
needed. This is a local skill project, not an uploaded/published marketplace plugin.

An explicit `--add-agent-rules` install adds a bounded routing block to the project
AGENTS.md or to `$CODEX_HOME/AGENTS.md` (`~/.codex/AGENTS.md` by default). It backs up
existing instructions and refuses malformed markers; it does not silently modify
an `AGENTS.override.md` which would shadow those rules [3]. Without this option,
no global Codex instructions or configuration are changed. Do not use the global
rules option for conflicting simultaneous user/project installations.

## Runtime data and coexistence

| Purpose | Windows | macOS |
| --- | --- | --- |
| Default skill | `%USERPROFILE%\.agents\skills\webuse-codex` | `~/.agents/skills/webuse-codex` |
| Runtime data | `%LOCALAPPDATA%\WebUseCodex` | `~/Library/Application Support/WebUseCodex` |
| Python environment | `<data>/.venv/Scripts/python.exe` | `<data>/.venv/bin/python` |
| Browser profile | `<data>/chrome-profile` | `<data>/chrome-profile` |
| Default memory | `<data>/Mem` | `<data>/Mem` |

Codex uses loopback CDP port **9223**, separated from the source edition's default
9222. Never copy a live Chrome profile between running browsers. A profile contains
session information; keep it private and do not include it in project archives.
Installation and upgrades never import example memory or overwrite an existing
Mem/profile. On the first task, select a Mem path and initialize it explicitly.

Path resolution order is `WEBUSE_CODEX_DATA_DIR`, legacy `WEBUSE_DATA_DIR`, the
installation metadata's `data_dir`, then the platform default. An explicit
`--data-dir` is persisted in the installed `.webuse-install.json`, so future shell
sessions do not need to re-export it. Clear a legacy override to keep editions
isolated. `WEBUSE_CDP_PROFILE`, `WEBUSE_CDP_ENDPOINT` and `WEBUSE_CDP_CHROME` are
optional browser overrides; a profile mismatch fails rather than taking control
of an unrelated instance. `WEBUSE_PYTHON` selects a Python executable for wrappers.

Reinstalling a managed skill preserves a copy of the previous code outside the
skill-scanning directory, under `.agents/.webuse-backups/`. An unmanaged target is
not overwritten. Keep personal changes in source control and merge them before
updating. Runtime files and skill files should not share a directory.

`--skip-deps` installs only the files; it does not imply that GUI dependencies or
permissions are ready. `--dry-run` displays paths without writing anything.

## Chinese text and native dialogs

Prefer CDP `fill`/`insert-text --input-file` for non-sensitive Unicode text. The
ASCII keyboard `type` command deliberately does not drive a Chinese IME. For a
native dialog only, and after verifying focus, a user-approved non-sensitive UTF-8
file can be pasted with the OS clipboard:

```powershell
Set-Clipboard -Value (Get-Content -Raw -Encoding UTF8 -LiteralPath '.\plain-text.txt')
& "$HOME\.agents\skills\webuse-codex\scripts\webuse.ps1" typing hotkey --keys primary v --json
```

```bash
pbcopy < './plain-text.txt'
bash "$HOME/.agents/skills/webuse-codex/scripts/webuse.sh" typing hotkey --keys primary v --json
```

Clipboard operations replace the user's clipboard. Do not use them for passwords,
authentication, payment details or other critical private information. Do not
silently read, save or restore unrelated private clipboard content.

## Remove the installed code

Close tasks using it, then remove only the installed `webuse-codex` skill folder.
If you opted into AGENTS rules, remove only the delimited `webuse-codex:start/end`
block. Runtime data is intentionally retained; inspect and manually delete it only
when you decide that the associated login profile and memory are no longer needed.
