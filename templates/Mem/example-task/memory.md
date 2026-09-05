# Task memory format

Template only. Replace placeholders with task-specific observations before recording.

## <recorded-at> - <short topic>

- status: candidate
- scope: <website, task, and conditions where this might apply>
- verified_on: <date only after actual verification>
- evidence: <observable result or source reference>
- expires_on: <optional date to review the advice>

Observation: <what actually happened>

Reusable step: <the smallest supported action or decision>

Verification: <how to confirm success on a future run>

Limits: <uncertainty, failure conditions, or prior record superseded>

Use `verified` only with evidence; use a new `stale` correction when an earlier observation no longer applies. Never interpret a stored workflow as external-action authorization.
