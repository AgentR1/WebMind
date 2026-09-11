# WebUse for Claude Code

WebUse is a Claude Code plugin for Windows and macOS. It packages six skills:
CDP browser control, desktop screenshots, mouse control, keyboard input,
two-second wait loops, and selective durable memory.

## Plugin layout

```text
.claude-plugin/plugin.json
skills/webuse-cdp/SKILL.md
skills/webuse-screenshot/SKILL.md
skills/webuse-mouse-control/SKILL.md
skills/webuse-typing/SKILL.md
skills/webuse-wait/SKILL.md
skills/webuse-mem/SKILL.md
scripts/
```

Run Claude Code against this local plugin during development:

```text
claude --plugin-dir /absolute/path/to/WebUse
```

## Install runtime dependencies

Windows PowerShell:

```powershell
& "$PWD\scripts\install.ps1"
```

macOS:

```bash
bash "$PWD/scripts/install.sh"
```

The installers create a private virtual environment in writable user data, not
inside the plugin. The default data locations are:

- Windows: `%LOCALAPPDATA%\WebUse`
- macOS: `~/Library/Application Support/WebUse`

Set `WEBUSE_DATA_DIR` to override the data root. The CDP Chrome profile and the
default `Mem` folder also live under this root.

## Unified launcher

Windows PowerShell:

```powershell
& "$env:CLAUDE_PLUGIN_ROOT\scripts\webuse.ps1" doctor
& "$env:CLAUDE_PLUGIN_ROOT\scripts\webuse.ps1" cdp self-check --json
```

macOS:

```bash
bash "$CLAUDE_PLUGIN_ROOT/scripts/webuse.sh" doctor
bash "$CLAUDE_PLUGIN_ROOT/scripts/webuse.sh" cdp self-check --json
```

Launcher components are `cdp`, `screenshot`, `mouse`, `typing`, and `mem`.
Python 3.10 or newer is required. GUI permissions are intentionally outside the
scope of this code-only setup.
