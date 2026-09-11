# webuse-typing

Codex Skill for real keyboard-like input automation.

## Install runtime dependency

Use the project-level platform installer in `scripts/` to install dependencies.

## Commands

```bash
webuse typing type --text "hello world"
webuse typing press --key enter
webuse typing hotkey --keys ctrl s
webuse typing down --key shift
webuse typing up --key shift
webuse typing list-keys
webuse typing self-check --json
```

Before any typing/key action, ensure the cursor/insertion point is in the correct target position and the active input method is English. If placement is uncertain, take a screenshot and focus/place the cursor first. Do not type Chinese text through this keyboard simulation skill.
