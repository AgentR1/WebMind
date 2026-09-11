> Component reference for the `webuse-codex` skill. Read the root `SKILL.md` first.
> `$WebUseRoot` (PowerShell) / `$WEBUSE_ROOT` (bash) is the absolute directory
> containing that root SKILL.md; derive it from the discovered skill path.
> These variables are assigned by the agent, not supplied by Codex.
> Use the root launchers so installation paths and UTF-8 are handled consistently.

# webuse-wait

Use `webuse-wait` when a Codex workflow needs to delay before the next development action while still keeping control of the task.

## Core rule

Wait in fixed 2-second increments. After every wait, inspect the relevant state and independently decide whether to continue waiting.

Do not ask the user whether to wait again after each 2-second interval.

## Required loop

```text
identify the condition being waited for
repeat:
    wait exactly 2 seconds
    inspect the relevant signal
    if the condition is satisfied:
        continue the original task
        stop this wait loop
    if another 2-second wait is still justified:
        continue the loop
    otherwise:
        stop waiting and report the current state
```

## Waiting command

Prefer the unified launcher: `webuse wait --json`, where `webuse` is shorthand
for the root platform launcher. It sleeps once for two seconds and returns;
Codex must inspect the state before invoking it again.

For an already authorized shell wait, the direct equivalent is:

```bash
sleep 2
```

In PowerShell, `Start-Sleep -Seconds 2` is the explicit equivalent.

Use another waiting primitive only when it also waits exactly 2 seconds for that cycle.

## What to inspect after each wait

Check at least one concrete signal before deciding to wait again:

- process status: still running, completed, failed, or stuck
- logs: new output, progress, error, or no change
- files: expected file, directory, artifact, or modification timestamp
- network: local port, endpoint, HTTP status, or readiness probe
- UI/browser: page reload, preview update, DOM/state change, or console output
- user constraints: max wait count, timeout, or explicit stop condition

## Continue waiting only when justified

Another 2-second wait is justified when at least one of these is true:

- the process is still active and appears healthy
- logs or output show recent progress
- a generated file or build artifact is still changing
- a server is starting and has not failed
- a user-provided timeout has not been reached and progress is plausible

## Stop waiting

Stop the loop when any of these is true:

- the awaited condition is satisfied
- the command exits successfully or fails
- repeated checks show no progress
- an error explains why waiting will not help
- there is no concrete signal to inspect
- the user-specified timeout or maximum wait count is reached

## Default safety behavior

If the user does not give a timeout, do not wait forever.

For quick UI, file, or browser state updates, stop after a few unchanged checks. For builds, installs, tests, or server startup, continue only while there is visible progress or a running process that appears healthy.

## Reporting when waiting stops unsuccessfully

When the condition is not satisfied, report briefly:

- what Codex waited for
- what signal was checked
- the latest observed state
- why another wait is not currently justified
- the next practical action
