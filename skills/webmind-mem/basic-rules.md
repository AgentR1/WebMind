# Global memory

Store only durable guidance that applies across users, machines, sites, and tasks.

## Browser modes / 浏览器使用模式

WebMind offers three user-facing modes. Interpret the user's choice as follows:

1. **用户自己浏览器模式 / User's own browser mode**: operate the user's already-open everyday browser through desktop screenshots, mouse and keyboard. Reuse its current session without attaching its everyday Profile to CDP.
2. **Agent 专用浏览器模式 / Dedicated Agent browser mode**: use a visible browser with the independent Profile bound to the selected Mem, operated through CDP/DOM. The user handles any required sign-in in that browser.
3. **不可见模式 / Invisible mode**: specifically run the dedicated Agent browser in Chrome **headless** mode (`--headless`), using the same Mem-bound independent Profile and CDP/DOM. It never means minimizing or obscuring a window, opening an inactive tab, or running an unrelated process in the background. It cannot be applied to the user's everyday browser.

WebMind 对用户提供三种使用模式，必须按以下含义理解用户的选择：

1. **用户自己浏览器模式**：通过桌面截图、鼠标和键盘操作用户已打开的日常浏览器，复用当前会话，不把日常 Profile 接入 CDP。
2. **Agent 专用浏览器模式**：使用所选 Mem 绑定的独立 Profile 打开可见浏览器，通过 CDP/DOM 操作；需要登录时由用户在该浏览器中完成。
3. **不可见模式**：用户提到“不可见模式”，明确指以 Chrome **headless** 模式（`--headless`）运行 **Agent 专用浏览器**，使用同一 Mem 绑定的独立 Profile，通过 CDP/DOM 操作。不代表最小化或遮挡窗口、不激活标签页、让其他进程在后台运行，也不能用于用户自己的日常浏览器。

- Choose invisible mode only when explicitly requested for the current task. Otherwise use a visible browser; never infer this choice from earlier tasks or save it as a default preference. Use the installed launcher's `cdp --invisible-mode` before every CDP subcommand in an invisible-mode task; keep Profile, port and actual-mode verification enabled.
- 每次任务只有用户明确要求时才使用不可见模式；未说明时使用可见浏览器，不沿用上次选择，不保存为默认偏好。不可见模式任务的每条 CDP 命令都要通过当前安装版本的启动器携带 `cdp --invisible-mode`，保留 Profile、端口和实际模式核验。
- Desktop screenshots, mouse and keyboard cannot operate the invisible page. Pause for a user-authorized transition to visible mode when manual authentication or takeover is needed; all privacy and authorization rules still apply.
- 桌面截图、鼠标和键盘不能操作不可见页面。需要人工认证或接管时，暂停并经用户授权切换到可见模式；所有隐私与授权规则继续适用。

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
