# webuse-mem

Codex skill for maintaining a user-specified external `Mem` folder for selective WebUse task memory.

The skill helps Codex:

- confirm the memory path before each concrete task
- initialize and validate the `Mem` folder
- read only global, content, and relevant task memories
- reconcile new evidence with old guidance at task end
- edit, reorder, replace, or remove obsolete experience instead of accumulating contradictions
- stop and escalate major unintended side effects before any refresh, retry, or remediation
- reuse a working retained login automatically; when login blocks the task, research a legitimate public alternative before asking the user to choose
- prohibit screenshots during authentication or critical-private-data entry, and never persist critical private information
- update `content.md` so the folder architecture stays visible

## External Mem structure

```text
Mem/
  global.md
  content.md
  <task-folder>/
    memory.md
    flow.md
    ui.md
    rules.md
    notes.md
```

Task folders are direct children of `Mem`.

## CLI

```bash
webuse mem --help
webuse mem init --mem-path /path/to/Mem --json
webuse mem list --mem-path /path/to/Mem --json
webuse mem search --mem-path /path/to/Mem --query "gmail" --json
webuse mem record --mem-path /path/to/Mem --task 发邮件 --file flow.md --stdin --json
webuse mem rewrite --mem-path /path/to/Mem --task 发邮件 --file flow.md --stdin --json
webuse mem rewrite-global --mem-path /path/to/Mem --stdin --json
```

No external dependencies are required.
