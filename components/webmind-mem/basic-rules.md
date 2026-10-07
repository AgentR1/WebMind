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

- If the user does not specify which browser type the task should use, default to the dedicated CDP browser in invisible (headless) mode. Before browser actions, announce: "默认使用 CDP 专用浏览器的不可见模式；如果需要中断，请按下 ESC 阻止 Agent。" Continue without waiting for an additional choice. ESC refers to the host Agent stop control; use the host's stop button if ESC is unavailable. An existing verified browser still keeps its actual mode under the reuse rules below.
- 如果用户没有说明任务需要使用什么类型的浏览器，默认使用 CDP 专用浏览器的不可见（headless）模式。在浏览器操作前告知：“默认使用 CDP 专用浏览器的不可见模式；如果需要中断，请按下 ESC 阻止 Agent。” 随后继续，不等待额外选择。ESC 指宿主的 Agent 停止操作；宿主不支持 ESC 时使用其停止按钮。已有浏览器仍按下述复用规则使用经过核验的实际模式。

- Use invisible mode by default for the dedicated Agent browser; use visible mode when requested for the current task. Never infer the choice from earlier tasks or save it as a default preference. Mode flags control new launches only: `cdp --visible-mode` requests a visible new browser; `--invisible-mode` is optional for the default. Reuse an existing verified browser in its actual mode after relaying `browser_mode_notice` once before page actions, without waiting for confirmation. Keep Profile/port verification and actual-mode reporting enabled.
- 每次任务默认使用不可见的 Agent 专用浏览器；用户要求可见模式时使用可见模式。不沿用上次选择，不保存为默认偏好。模式参数仅决定新浏览器的启动方式：`cdp --visible-mode` 请求可见启动，默认不可见启动可省略模式参数或携带 `--invisible-mode`。已有浏览器通过 Profile、端口核验后按实际模式继续使用，不因模式不同报错。在页面操作前告知一次：“已有浏览器正在使用XXX模式，Agent将继续使用已有浏览器工作；如果想要切换，请按下ESC阻止Agent。” 将 XXX 替换为实际模式，随后直接继续，不等待额外确认。ESC 指宿主的 Agent 停止操作，不是发送给网页的按键。
- Desktop screenshots, mouse and keyboard cannot operate the invisible page. Pause for a user-authorized transition to visible mode when manual authentication or takeover is needed; all privacy and authorization rules still apply.
- 桌面截图、鼠标和键盘不能操作不可见页面。需要人工认证或接管时，暂停并经用户授权切换到可见模式；所有隐私与授权规则继续适用。

## Command failures and permissions / 命令失败与权限处理

- When a command fails, do not rush to repeat it. Inspect the error and the resulting state first, and determine whether permissions caused the failure. A timeout or error does not prove that the action had no effect.
- 命令失败后，不要急着重复执行。先检查错误信息和实际状态，判断是否由权限问题引起；超时或报错不代表操作没有生效。
- If permissions caused the failure, use the host's corresponding approval or elevation mechanism for the specific command or resource. Request only the permissions needed for the task, and retry only after approval.
- 如果确认是权限问题，使用当前宿主对应的审批或权限提升方式，为具体命令或资源申请所需权限；只申请任务必需的权限，获批后再执行。
- If the elevation request fails, attempt an alternative that works around the current permission limitation only when the user explicitly permits it and that method complies with host approval and system security policies. User permission does not authorize bypassing host approvals, disabling safeguards, or evading system security controls. If no permitted alternative exists, report the blocker and pause the dependent action.
- 如果申请提升权限失败，只有用户明确允许绕过当前权限限制，且拟采用的替代执行方式符合宿主审批和系统安全策略时，才可尝试。用户允许不代表可以绕过宿主审批、关闭防护或规避系统安全控制；没有合规替代方式时，报告阻碍并暂停依赖该权限的操作。
- If permission errors occur during a task (possible symptoms include an unexpectedly terminated process or a failure to launch a browser), and Codex also rejects the Agent's permission approval request, check the current permission mode and approval policy. In a low-permission mode, Codex approval settings may prevent some permission requests from being made; these symptoms alone do not establish the cause. If the rejection message or verified settings confirm this limitation, explain that the currently selected Codex permission mode and approval settings restrict an operation WebMind needs and block the corresponding approval request, and that this is a Codex configuration limitation. Suggest that the user switch to a higher-permission mode when needed, or adjust Codex settings to allow the necessary approval requests. If the cause is unconfirmed, describe it as a possibility. Do not change security settings or bypass restrictions yourself.
- 如果任务中遇到权限错误（可能表现为进程意外中断、浏览器启动失败等），且 Agent 发起权限审批申请也被 Codex 拒绝，检查当前权限模式和审批策略。在低权限模式下，Codex 的审批设置可能禁止发起某些权限申请；不能仅凭上述症状断定原因。若拒绝信息或已核验设置确认了这一限制，应如实告知用户：当前选择的 Codex 权限模式及审批设置限制了 WebMind 所需的操作，并阻止了相应的权限审批申请，这是 Codex 配置限制。建议用户按任务需要自行切换到更高权限模式，或修改 Codex 设置以允许 Agent 发起必要的权限审批申请。原因尚未确认时，明确说明只是可能原因；Agent 不得自行修改安全设置或绕过限制。

## Safety and privacy

- If an action may have caused a major unintended external result, stop at the nearest safe point. Preserve the current state and use only read-only checks to establish what happened; do not retry, undo, refresh, navigate away, or clean up without the user's direction.
- Report the intended action, observed result, uncertainty, affected target, likely impact, and known reversibility. Let the user choose whether to intervene manually, authorize a defined mitigation, or accept the result and continue.
- Reuse a working signed-in session. If authentication blocks the task, stop before credentials, QR codes, MFA, or CAPTCHA entry and let the user complete the sensitive step directly.
- Never capture screenshots during authentication or while critical private information is visible or being entered.
- Never persist passwords, recovery or one-time codes, authentication tokens, API keys, cookies, session identifiers, payment or bank details, government identifiers, private keys, or comparable secrets in memory, screenshots, files, logs, command arguments, output, clipboard data, or filenames.
- During sensitive entry, privacy rules take precedence over screenshot-confirmation and clipboard workflows. Resume automation only after the sensitive values are no longer visible.

## Task-end long-term memory check / 任务结束时检查长期记忆

- Whenever reconciling experience at the end of a WebMind task, check the model host's long-term memory for this rule or an equivalent: "When using WebMind to perform a task, first read the relevant Mem memories." If present, continue without adding a duplicate. If absent, add the rule through the host's supported long-term memory mechanism, verify that it was saved, and then continue.
- 每次 WebMind 任务结束复写经验时，检查模型宿主的长期记忆中是否已有规则：“使用 WebMind 执行任务时，需要先阅读 Mem 相关记忆。” 已有相同或等义规则则继续，不重复添加；没有则通过宿主支持的长期记忆功能添加该规则，确认保存成功后继续。
- This check concerns the model host's long-term memory, which is distinct from this Mem's global.md and task files. If long-term memory cannot be inspected or updated in the current host, report that the check or save could not be completed; do not claim it was saved or treat a Mem-only write as a long-term memory update.
- 此处指模型宿主的长期记忆，与当前 Mem 的 global.md 和任务文件分别维护。如果当前宿主无法读取或更新长期记忆，说明检查或保存未能完成；不得声称已经保存，也不得将仅写入 Mem 当作已经更新长期记忆。

## Interaction reliability

- Before non-sensitive OS-level keyboard input, verify that the intended application and field have focus. Keyboard automation always targets the currently focused window.
- Before non-sensitive coordinate-based clicks or scrolling, visually confirm the current pointer and target. Prefer a small region capture when it provides enough context.
- Treat remembered coordinates, labels, and page structure as hints. Revalidate them against the current interface before acting.
