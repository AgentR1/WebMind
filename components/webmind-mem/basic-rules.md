# Global memory

Store only durable guidance that applies across users, machines, sites, and tasks.

## Browser modes / 浏览器使用模式

WebMind offers three user-facing modes. Interpret the user's choice as follows:

1. **用户自己浏览器模式 / User's own browser mode**: operate the user's already-open everyday browser through desktop screenshots, mouse and keyboard. Reuse its current session without attaching its everyday Profile to CDP.
2. **Agent 专用浏览器模式 / Dedicated Agent browser mode**: use the independent Profile bound to the selected Mem through CDP/DOM, in invisible mode by default. Choose visible mode with `--visible-mode` for manual sign-in or takeover.
3. **不可见模式 / Invisible mode**: specifically run the dedicated Agent browser in Chrome **headless** mode (`--headless`), using the same Mem-bound independent Profile and CDP/DOM. It never means minimizing or obscuring a window, opening an inactive tab, or running an unrelated process in the background. It cannot be applied to the user's everyday browser.

WebMind 对用户提供三种使用模式，必须按以下含义理解用户的选择：

1. **用户自己浏览器模式**：通过桌面截图、鼠标和键盘操作用户已打开的日常浏览器，复用当前会话，不把日常 Profile 接入 CDP。
2. **Agent 专用浏览器模式**：使用所选 Mem 绑定的独立 Profile，通过 CDP/DOM 操作，默认不可见；需要人工登录或接管时，通过 `--visible-mode` 切换到可见模式。
3. **不可见模式**：用户提到“不可见模式”，明确指以 Chrome **headless** 模式（`--headless`）运行 **Agent 专用浏览器**，使用同一 Mem 绑定的独立 Profile，通过 CDP/DOM 操作。不代表最小化或遮挡窗口、不激活标签页、让其他进程在后台运行，也不能用于用户自己的日常浏览器。

- Use invisible mode by default for the dedicated Agent browser; use visible mode when requested for the current task. Never infer the choice from earlier tasks or save it as a default preference. Mode flags control new launches only: `cdp --visible-mode` requests a visible new browser; `--invisible-mode` is optional for the default. Reuse an existing verified browser in its actual mode after relaying `browser_mode_notice` once before page actions, without waiting for confirmation. Keep Profile/port verification and actual-mode reporting enabled.
- 每次任务默认使用不可见的 Agent 专用浏览器；用户要求可见模式时使用可见模式。不沿用上次选择，不保存为默认偏好。模式参数仅决定新浏览器的启动方式：`cdp --visible-mode` 请求可见启动，默认不可见启动可省略模式参数或携带 `--invisible-mode`。已有浏览器通过 Profile、端口核验后按实际模式继续使用，不因模式不同报错。在页面操作前告知一次：“已有浏览器正在使用XXX模式，Agent将继续使用已有浏览器工作；如果想要切换，请按下ESC阻止Agent。” 将 XXX 替换为实际模式，随后直接继续，不等待额外确认。ESC 指宿主的 Agent 停止操作，不是发送给网页的按键。
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
