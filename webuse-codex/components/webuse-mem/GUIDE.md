> Component reference for the `webuse-codex` skill. Read the root `SKILL.md` first.
> `$WebUseRoot` (PowerShell) / `$WEBUSE_ROOT` (bash) is the absolute directory
> containing that root SKILL.md; derive it from the discovered skill path.
> These variables are assigned by the agent, not supplied by Codex.
> Use the root launchers so installation paths and UTF-8 are handled consistently.

# webuse-mem

Use this skill when Codex needs selective, durable memory for WebUse-style tasks. The memory lives outside the skill in a folder named `Mem`. Treat memory as a maintained guide, not an append-only activity log.

## Cross-platform launcher

Commands below use `webuse` as shorthand. Translate `webuse mem ...` to:

```powershell
& "$WebUseRoot\scripts\webuse.ps1" mem <command> [options]
```

```bash
bash "$WEBUSE_ROOT/scripts/webuse.sh" mem <command> [options]
```

Do not depend on the current working directory. `--mem-path` is optional; its
default is `%LOCALAPPDATA%\WebUseCodex\Mem` on Windows and
`~/Library/Application Support/WebUseCodex/Mem` on macOS. The root launcher also
respects the installed data path, `WEBUSE_CODEX_DATA_DIR`, and the legacy
`WEBUSE_DATA_DIR` override. Inspect `doctor` for the actual resolved location.

## Codex workflow trigger

When Codex selects `$webuse-codex` for a concrete local browser/GUI task, run this
memory workflow at task start and task end. This component is a reference, not an
independently registered skill or an automatic background hook. Use the root
skill's description and optional AGENTS routing block to select the workflow.
Do not trigger memory for unrelated coding or ordinary web research. Do not
re-confirm a path that the user already explicitly selected for the same task.

## Mem path selection rule

Use the Mem folder explicitly provided by the user. Otherwise use the script's
platform default in writable user data. Do not automatically select a `Mem`
folder bundled beside skill source code, because skill files may be read-only
or replaced during an update.

If the provided path does not end with `Mem`, let the script normalize it to `<path>/Mem` and respect the warning it returns.

## Do not load unrelated memory

- Use this skill automatically only after the task is concrete enough to choose relevant memory.
- Do not inspect unrelated task folders.
- At task start, read only `global.md`, `content.md`, and task folders that are plausibly relevant to the current task.
- If no relevant task folder exists, proceed without old task memory and create one only when useful at task end.

## Major side-effect incident rule

If an action causes, or is reasonably suspected to have caused, a major unintended external result—such as sending a message or email to the wrong recipient, deleting or overwriting data, uploading or sharing the wrong file, publishing unintended content, or repeating a consequential submission—stop the automation at the nearest safe point.

Do not immediately refresh, navigate away, retry, resubmit, repeat the original action, or attempt an undo or cleanup. The original task authorization does not authorize remediation, and refreshing may hide evidence or repeat the side effect.

Before asking the user, perform only safe, read-only observation needed to understand the incident. Preserve the visible state when practical and record, without exposing secrets:

- the intended action and what actually happened
- the known cause, or clearly labeled inference or uncertainty
- the affected target, data, or recipient
- the known and reasonably possible impact
- whether the side effect appears completed, ongoing, reversible, or unknown

Tell the user promptly and ask them to choose the next course:

1. the user intervenes manually
2. the user explicitly authorizes the agent to attempt a defined mitigation
3. the user accepts the impact and explicitly authorizes the agent to refresh or retry

Do not choose among these options for the user. Until the user decides, make no further external-state changes related to the incident. After the choice, act only within the selected scope; obtain new authorization if mitigation introduces another material or irreversible side effect.

At task end, store only a durable prevention or recovery lesson after the incident is understood. Do not store private incident details, and reconcile the lesson with existing guidance instead of appending a contradictory incident log.

## Authentication-gate rule

First inspect whether the current website session is already authenticated or whether the required content and action are available without another sign-in. If the site is already signed in, or a retained session is working, reuse that session and continue the task automatically. In this case, do not search for an alternative and do not ask the user to choose.

Only when sign-in actually blocks the required task:

1. Stop before entering credentials, scanning a QR code, completing MFA, or handling a CAPTCHA on the user's behalf.
2. Search for a legitimate, publicly accessible way to achieve the requested outcome without signing in. Use only read-only research, do not disclose private task data, and do not bypass authentication, paywalls, permissions, or access controls.
3. If a viable method is found, explain: `The alternative I found is: ...` Include its source, what it can accomplish, and any material limitation in freshness, completeness, privacy, or output quality.
4. Ask the user to choose exactly one next path:
   - **A.** The user signs in manually, then the agent continues with the original method.
   - **B.** The agent tries the explained no-sign-in method within the original task scope.
5. If no viable no-sign-in method is found, say so clearly and ask the user to sign in manually before continuing; do not offer a non-viable option B.

Do not select A or B for the user. If the user chooses A, wait until they confirm or the site visibly shows a usable authenticated session. If the user chooses B, use only the method already explained; ask again before switching to a materially different workaround.

The major side-effect incident rule takes precedence. A login prompt that appears while preserving or investigating a consequential error does not authorize navigating away, refreshing, or starting alternative research in the affected session.

## Sensitive-entry and privacy rule

During any sign-in, account-recovery, MFA, CAPTCHA, payment-authentication, or other authentication flow, do not capture or save screenshots. This prohibition applies even when fields are blank or values are masked, and includes full-screen, region, browser, CDP, and OS-level screenshots.

Also do not capture screenshots while critical private information is visible or being entered. Critical private information includes passwords, one-time or recovery codes, authentication tokens, API keys, cookies or session identifiers, payment-card or bank details, government identifiers, private cryptographic keys, and similarly sensitive personal records.

The agent MUST NOT persist critical private information in `Mem`, screenshots, saved page/PDF content, logs, summaries, command arguments or output, clipboard contents, filenames, or temporary files. Do not ask the user to paste such information into chat, do not echo it back, and do not read field values for verification. The user must enter it directly in the target application.

When an existing visual or keyboard workflow normally requires screenshot confirmation, the privacy rule takes precedence: do not use that workflow during the sensitive phase. Pause and let the user complete the sensitive step. Resume screenshots only after authentication or sensitive entry is complete and the page no longer displays the critical values; confirm this without reading or reproducing those values.

Existing screenshot and clipboard guidance continues to apply to non-sensitive content. If a prohibited screenshot or other privacy-bearing artifact is accidentally created, treat it as a major side-effect incident: do not reopen, copy, upload, or share it; report what was created and wait for the user to choose manual handling or explicitly authorize a defined cleanup.

## Mem folder structure

The external memory folder MUST be named `Mem` and SHOULD have this structure:

```text
Mem/
  global.md        # global instructions and durable cross-task memory
  content.md       # current architecture/index of this Mem folder
  <task-folder>/   # one folder per reusable task category, such as Gmail or Zhihu
    memory.md      # concise stable memory for the task
    flow.md        # proven workflow steps
    ui.md          # button shapes, visible labels, approximate positions, page clues
    rules.md       # task-specific rules and constraints
    notes.md       # optional extra durable notes
```

Task folders live directly under `Mem`; do not add an extra `tasks/` wrapper unless the user explicitly asks.

## What to remember

At the end of every completed concrete task, Codex MUST review the task and decide what belongs in memory. Record only information that is durable, reusable, and likely to help a future Codex task. New evidence may require editing, reordering, replacing, or removing old guidance rather than appending another dated note.

Good memory candidates:

- stable workflows that succeeded
- site/app-specific navigation steps
- button labels, shapes, visual positions, and screenshots-to-coordinate reasoning that are likely to stay useful
- stable constraints, preferences, naming conventions, or user-approved rules
- verified fixes or avoidance rules for recurring problems

Do not record:

- passwords, tokens, cookies, verification codes, secrets, private account data, credentials, or any other critical private information covered by the privacy rule
- one-time task output, temporary IDs, transient page state, or stale coordinates that were not generally useful
- speculative reasoning, failed attempts, or errors unless distilled into a stable, reusable avoidance rule
- information from unrelated tasks

## Canonical-memory consistency rules

Before changing memory, reread every relevant file in the selected task folder and any directly applicable global rule. Reconcile the whole guidance set, not just the newest note.

- For the same goal under the same conditions, there MUST be exactly one default, preferred, recommended, or first-choice method.
- If a newly verified method is better, make it the sole preferred method. Keep the old method only when it remains useful as an explicitly ranked fallback, and state the condition that justifies using it.
- If two methods are best in different situations, state the mutually distinguishable conditions. Do not present both as unconditional first choices.
- Merge complementary guidance, remove duplicates, and delete guidance that is obsolete, disproved, or fully superseded.
- Resolve conflicts across `memory.md`, `flow.md`, `ui.md`, `rules.md`, and applicable `global.md`; do not repair one file while leaving another contradictory instruction behind.
- Prefer descriptive headings and a coherent current procedure over a chronology of dated updates. Keep dates only when recency affects validity.
- Do not promote uncertain or unverified observations into canonical guidance. If evidence is insufficient to choose between conflicting methods, leave memory unchanged rather than storing a contradiction.

After editing, reread the complete affected task memory and verify that priorities, conditions, terminology, and step order agree. A successful CLI response does not replace this semantic review.

## Program file

Run the bundled Python program from the skill folder:

```bash
webuse mem --help
```

No external Python packages are required.

## Commands

### 1. Check environment

```bash
webuse mem self-check --json
```

With a path:

```bash
webuse mem self-check --mem-path /path/to/Mem --json
```

### 2. Initialize or repair the Mem folder

Use the selected Mem path:

```bash
webuse mem init --mem-path /path/to/Mem --json
```

If the provided path does not end with `Mem`, the script treats it as a parent directory and uses `<path>/Mem`, returning a warning in JSON.

### 3. Check existing structure

```bash
webuse mem check --mem-path /path/to/Mem --json
```

Use `--create-missing` only for the default path or for a path the user explicitly provided:

```bash
webuse mem check --mem-path /path/to/Mem --create-missing --json
```

### 4. Refresh `content.md`

Run this after creating, renaming, deleting, or updating task folders:

```bash
webuse mem rebuild-content --mem-path /path/to/Mem --json
```

### 5. List task folders

```bash
webuse mem list --mem-path /path/to/Mem --json
```

Use this together with `content.md` to decide which task folder is relevant.

### 6. Search relevant memory

Search only after the task is clear:

```bash
webuse mem search --mem-path /path/to/Mem --query "send email" --json
```

Use search results to choose a small number of relevant files to read. Do not treat search hits as permission to inspect unrelated memories.

### 7. Read memory

Read global memory:

```bash
webuse mem read --mem-path /path/to/Mem --scope global
```

Read the folder index:

```bash
webuse mem read --mem-path /path/to/Mem --scope content
```

Read all markdown files in one relevant task folder:

```bash
webuse mem read --mem-path /path/to/Mem --task Gmail
```

Read one specific file inside a relevant task folder:

```bash
webuse mem read --mem-path /path/to/Mem --task Gmail --file flow.md
```

### 8. Append non-conflicting task memory

Prepare the memory block in a UTF-8 Markdown file, then pipe it through the
platform launcher. This avoids shell-specific heredocs and works on both OSes.

```powershell
Get-Content -Raw -LiteralPath .\memory-update.md | & "$WebUseRoot\scripts\webuse.ps1" mem record --task Gmail --file flow.md --title "gmail compose flow" --stdin --json
```

```bash
cat ./memory-update.md | bash "$WEBUSE_ROOT/scripts/webuse.sh" mem record --task Gmail --file flow.md --title "gmail compose flow" --stdin --json
```

Use separate files when helpful:

```bash
webuse mem record --mem-path /path/to/Mem --task Zhihu --file ui.md --title "search box visual cue" --stdin --json
```

Use `record` for a new file or a genuinely independent addition. Do not append overlapping guidance when it would create duplicate priorities or preserve a superseded instruction. The script creates the task folder when needed and refreshes `content.md` after recording.

### 9. Reconcile an existing task memory file

Read the complete file, produce its complete canonical replacement, and pass that replacement to `rewrite`. Removing a passage from the replacement is the supported way to delete obsolete experience while keeping the remaining document coherent.

```powershell
Get-Content -Raw -LiteralPath .\complete-reconciled-flow.md | & "$WebUseRoot\scripts\webuse.ps1" mem rewrite --task Gmail --file flow.md --stdin --json
```

```bash
cat ./complete-reconciled-flow.md | bash "$WEBUSE_ROOT/scripts/webuse.sh" mem rewrite --task Gmail --file flow.md --stdin --json
```

`rewrite` requires an existing file, rejects empty Markdown or Markdown without a level-1 heading, writes atomically, and refreshes `content.md`. Use `--expected-sha256 <hash>` when concurrent changes are possible; the command then refuses to overwrite a file that changed after it was read.

### 10. Record or reconcile global memory only when truly global

```powershell
Get-Content -Raw -LiteralPath .\global-update.md | & "$WebUseRoot\scripts\webuse.ps1" mem record-global --title "global rule" --stdin --json
```

```bash
cat ./global-update.md | bash "$WEBUSE_ROOT/scripts/webuse.sh" mem record-global --title "global rule" --stdin --json
```

Only write global memory for rules that should apply across many unrelated tasks.

When an existing global rule must be updated or removed, rewrite the complete reconciled `global.md`:

```powershell
Get-Content -Raw -LiteralPath .\complete-reconciled-global.md | & "$WebUseRoot\scripts\webuse.ps1" mem rewrite-global --stdin --json
```

```bash
cat ./complete-reconciled-global.md | bash "$WEBUSE_ROOT/scripts/webuse.sh" mem rewrite-global --stdin --json
```

## Task-start workflow

```text
1. Confirm the task is concrete enough to benefit from memory.
2. Use the user-provided Mem path when present; otherwise use the platform default.
3. Run init/check on the selected Mem path.
4. Read global.md.
5. Read content.md or list/search to find relevant task folders.
6. Read only the selected relevant task memories.
7. Perform the task using the loaded memory plus current observation.
```

## Task-end workflow

If a major side-effect incident occurred, complete the incident rule and obtain the user's disposition before consolidating memory or resuming the original workflow.

```text
1. Review what actually happened in the task.
2. Reread all relevant task files and directly applicable global guidance.
3. Classify new evidence as confirming, complementary, superseding, or invalidating old guidance.
4. Build one coherent canonical result: one preferred method per matching scenario, explicitly ordered fallbacks, and explicit conditions for context-dependent alternatives.
5. Use record only for independent additions; use rewrite/rewrite-global to edit, reorder, replace, or remove overlapping guidance.
6. Reread the final affected memory as a whole and resolve every remaining contradiction, duplicate priority, stale cross-reference, and inconsistent step order.
7. Confirm content.md is refreshed.
8. Report which files were added, rewritten, or left unchanged, or report that nothing durable was learned.
```

## Output behavior

Use `--json` for machine-readable results. Successful JSON responses include `ok: true`, the action name, the normalized Mem path, and command-specific details. Failed commands exit non-zero and return either an error message or `ok: false` when `--json` is used.
