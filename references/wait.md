# Waiting for observable progress

Wait is a workflow rule, not a separate Python command or background scheduler. Use it when a browser, local server, build, file, or application needs time to reach a specific state.

1. Name the condition to observe, such as an element appearing, a process exiting, or a generated file becoming available.
2. Set an overall deadline or maximum number of checks before starting.
3. Wait for two seconds using the host's available wait primitive, then inspect that condition.
4. Continue the original task as soon as the condition is met. Stop early on a failure, cancellation, or evidence that another wait will not help.

For a shell-based workflow, one wait cycle is:

```bash
sleep 2
```

For a host without that shell command, use an equivalent two-second wait. The state check must happen after each cycle; do not replace it with a long blind sleep. For deadline enforcement, count elapsed time with a monotonic clock, including the observation time. A final shortened wait is appropriate when fewer than two seconds remain.

Useful observations include process exit status, new log output, expected files and timestamps, an endpoint readiness response, or a fresh DOM / screenshot inspection. Choose one that demonstrates the required state, rather than treating elapsed time as proof of readiness.

For webpage readiness, prefer Core's bounded `wait-for-selector` or `read-page --wait-selector` commands. For an existing host tool that already waits for completion, use its bounded wait interface instead of adding a second polling loop. This guidance does not require changing those tools' internal polling intervals.

Without a user-specified timeout, choose a finite limit appropriate to the operation. Stop after several unchanged checks for a small UI update; for a build or installation, continue only while a live process or observable progress supports waiting. Report the last observation, elapsed time, and the next practical step if the condition is not met. Do not ask for confirmation after every two-second cycle.

Return to the [suite README](../README.md).
