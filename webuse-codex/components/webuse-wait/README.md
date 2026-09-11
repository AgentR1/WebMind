# webuse-wait

Skill for controlled 2-second wait cycles, designed around Codex development workflows.

The skill tells the agent to:

1. wait exactly 2 seconds,
2. inspect the relevant condition,
3. decide by itself whether to wait another 2 seconds,
4. stop when the condition is satisfied or further waiting is not useful.

This package is intentionally built for Codex-oriented usage and keeps the requested `webuse-wait` naming.
