# Global memory

Store only durable guidance that applies across users, machines, sites, and tasks.

## Safety and privacy

- If an action may have caused a major unintended external result, stop at the nearest safe point. Preserve the current state and use only read-only checks to establish what happened; do not retry, undo, refresh, navigate away, or clean up without the user's direction.
- Report the intended action, observed result, uncertainty, affected target, likely impact, and known reversibility. Let the user choose whether to intervene manually, authorize a defined mitigation, or accept the result and continue.
- Reuse a working signed-in session. If authentication blocks the task, stop before credentials, QR codes, MFA, or CAPTCHA entry and let the user complete the sensitive step directly.
- Never capture screenshots during authentication or while critical private information is visible or being entered.
- Never persist passwords, recovery or one-time codes, authentication tokens, API keys, cookies, session identifiers, payment or bank details, government identifiers, private keys, or comparable secrets in memory, screenshots, files, logs, command arguments, output, clipboard data, or filenames.
- During sensitive entry, privacy rules take precedence over screenshot-confirmation and clipboard workflows. Resume automation only after the sensitive values are no longer visible.

## Interaction reliability

- Before non-sensitive OS-level keyboard input, verify that the intended application and field have focus. Keyboard automation always targets the currently focused window.
- Before non-sensitive coordinate-based clicks or scrolling, visually confirm the current pointer and target. Prefer a small region capture when it provides enough context.
- Treat remembered coordinates, labels, and page structure as hints. Revalidate them against the current interface before acting.
