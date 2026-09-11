# WebUse for Codex repository

For an authorized local browser or desktop task, read `SKILL.md` and follow the
`webuse-codex` workflow: selected Mem first, CDP before GUI, verify the result, and
reconcile only reusable memory at the end. The runtime must run on the same
native Windows/macOS desktop as the target applications. Ask for narrowly scoped
permissions when needed; do not edit security settings to work around a denial.

For development, preserve all six capability modules under `components/`.
Use UTF-8 without BOM and LF for source files, and invoke platform launchers via
their absolute paths. Do not introduce a dependency on a host plugin-root variable.
Run `python -B scripts/run_tests.py`; opt into browser tests only with a disposable
local browser. Preserve browser profile validation, privacy rules and failsafes.
Never modify `examples/Mem` as though it were the user's active memory.

This file is scoped to this repository. The installer does not alter global Codex
instructions or config unless the user explicitly supplies `--add-agent-rules`.
