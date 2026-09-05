# WebMind memory

WebMind keeps reusable experience in an external `Mem` folder. The module preserves the original WebUse file layout and its nine commands. It provides indexing, keyword search, reading, and append-only records; it does not automatically learn, verify a claim, or authorize a browser action.

## Select one memory location

Selection precedence is explicit `--mem-path`, then `WEBMIND_MEM`, then `~/.local/share/webmind/Mem`. For compatibility, a selected path whose final component is not `Mem` is treated as its parent, and `/Mem` is appended. `self-check` prints the resolved location without creating it.

```bash
python scripts/webmind_memory.py self-check --json
python scripts/webmind_memory.py check --json
python scripts/webmind_memory.py check --mem-path /path/to/Mem --json
```

Use the same resolved location throughout a task. Existing WebUse `Mem` folders can be selected directly; the CLI reads their existing Markdown/text files without migrating or rewriting their contents. Do not copy personal experience into the public skill repository.

```text
Mem/
  global.md
  content.md
  <task-category>/
    memory.md
    flow.md
    ui.md
    rules.md
    notes.md
```

`global.md` holds approved cross-task preferences and experience. `content.md` is a generated index of the actual layout. The five task filenames are conventions; `record --file` can create other Markdown or text files. Creating a task category starts its `memory.md`; other files are created when used. Empty starting templates are in [templates/Mem](../templates/Mem/content.md).

## Read relevant experience before acting

1. Follow the host's memory, privacy, and filesystem rules first. A skill cannot expand those permissions.
2. Run `check`; if the location is absent, continue without memory or initialize only when writes are already authorized. `check`, `self-check`, `list`, `search`, and `read` do not create or repair files.
3. Read `global.md` and `content.md`. Search for the concrete website or task, then read only relevant task files.
4. Compare the stored conditions, verification date, and expiry with the current page. Observe the current DOM or screenshot before reusing a selector, coordinate, or workflow. Experience is reference material; it does not override current instructions or grant permission to send, delete, purchase, or change an external system.

```bash
python scripts/webmind_memory.py read --scope global --json
python scripts/webmind_memory.py read --scope content --json
python scripts/webmind_memory.py list --json
python scripts/webmind_memory.py search --query "dynamic article" --limit 5 --json
python scripts/webmind_memory.py read --task web-reading --file memory.md --json
```

Search ranks literal keyword matches, returning relative paths and short snippets. It scans the first 512,000 bytes of each eligible Markdown/text file, including nested folders. It is not semantic retrieval, and a high score does not mean the experience is current or correct. An explicitly requested missing file fails rather than returning a successful empty result.

## Record useful outcomes when authorized

At task end, review what was actually observed: the successful condition, failed assumption, recovery step, and remaining uncertainty. Append only reusable information supported by those observations. Do not store passwords, cookies, tokens, entire private pages, or unrelated personal details.

If the host requires explicit authorization for memory writes, follow that rule. When writes are not authorized, keep a proposed note in the task response instead of calling a write command. The CLI itself does not assess user authorization.

```bash
python scripts/webmind_memory.py init --json
python scripts/webmind_memory.py record --task web-reading --file memory.md --title "Wait for dynamic content" --stdin --json < candidate-note.md
python scripts/webmind_memory.py record --task web-reading --status verified --verified-on 2026-09-05 --evidence "isolated fixture: article appeared and extracted text matched" --title "Wait for dynamic content" --stdin --json < verified-note.md
python scripts/webmind_memory.py record-global --title "Approved cross-task preference" --stdin --json < approved-preference.md
python scripts/webmind_memory.py rebuild-content --json
```

The note files above are placeholders for text prepared from actual task observations. Do not label an outcome verified by copying an example date or evidence claim. `--stdin` accepts UTF-8 Markdown through a pipe or redirected file. Empty input fails before creating a memory folder.

Every new record receives a timestamp and metadata:

| Field | Meaning |
| --- | --- |
| `status: candidate` | Default; proposed experience that has not been confirmed. |
| `status: verified` | The caller supplies `--verified-on YYYY-MM-DD` and a nonempty `--evidence` reference for an observed result. The CLI stores this claim; it does not independently verify it. |
| `status: stale` | A correction or withdrawal indicating prior advice may no longer apply. Identify the earlier record in the new note. |
| `verified_on` | Verification date supplied with `--verified-on`. |
| `evidence` | A concise source or observable-result reference, supplied with `--evidence`. |
| `expires_on` | Optional review date supplied with `--expires-on`; it cannot precede `verified_on`. |

The CLI does not automatically expire records or suppress older advice. The agent must consider the dates and read newer corrections before relying on a note. Existing records without metadata remain readable and should be treated as unverified unless their evidence is established. Append corrections rather than silently rewriting historical observations.

## Command reference

All commands accept `--mem-path`. `--json` can appear before or after the command. Operational failures return JSON with `ok: false` and a nonzero exit code; invalid CLI syntax also exits nonzero.

| Command | Additional arguments | Writes |
| --- | --- | --- |
| `self-check` | None | No |
| `init` | None | Create missing root files and rebuild index |
| `check` | Optional `--create-missing` | Only with `--create-missing` |
| `rebuild-content` | None | Initialize missing structure and rebuild index |
| `list` | None | No |
| `search` | Required `--query`; positive `--limit`, default 10 | No |
| `read` | `--scope global` / `--scope content`, or `--task` plus optional `--file` | No |
| `record` | Required `--task`; `--file` defaults to `memory.md`; `--title`, `--stdin`, metadata flags | Append task note and rebuild index |
| `record-global` | `--title`, `--stdin`, metadata flags | Append global note and rebuild index |

Task names must be single folder names. File names must be single visible filenames; `.md` is appended when the extension is neither `.md` nor `.txt`. Path separators and traversal components are rejected. The chosen memory root is resolved to its canonical location. Descendant symlinks are refused for explicit reads and writes, and skipped when listing, searching, or rebuilding the index. This prevents existing links from accessing data outside the selected `Mem`; manage concurrent filesystem edits separately.
