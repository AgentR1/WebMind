> 提示：切换 branch 可以切换不同操作系统版本，包括 macOS 或 Windows 下的 Claude Code 版和 Codex 版。
>
> Tip: Switch branches to change between the Claude Code and Codex editions for macOS or Windows.
>
> 你现在看到的是 Windows 下的 Codex 版，版本号 WX 1.0.0。
>
> You are viewing the Codex edition for Windows, version WX 1.0.0.

# WebMind for Codex — Windows

面向原生 Windows 桌面的 Codex Skill：通过经过 Profile 核验的 CDP/DOM 控制浏览器，并在必要时使用截图、鼠标、键盘、有界等待和外部 Mem。

A Codex Skill for the native Windows desktop. It controls the browser through profile-verified CDP/DOM and uses screenshots, mouse and keyboard input, bounded waits, and external Mem when necessary.

> [!WARNING]
> 本项目可以改变网页、账号和桌面状态。安装前请完整阅读 [使用教程](使用教程.md) 与 [安全须知](安全须知.md)。不要跳过首次风险接受和外部 Mem 选择。
>
> This project can change webpages, accounts, and desktop state. Before installation, read the [User Guide](User%20Guide.md) and [Safety Instructions](Safety%20Instructions.md) in full. Do not skip first-use risk acceptance or external Mem selection.

## 运行要求 / Requirements

- Windows 10/11 的本地可见桌面会话（不支持 WSL、云端容器或远程控制另一台电脑）

  A visible local desktop session on Windows 10/11; WSL, cloud containers, and remote control of another computer are unsupported.
- Codex 桌面版、CLI 或 IDE 扩展

  Codex desktop, CLI, or IDE extension.
- Python 3.10 或更高版本

  Python 3.10 or later.
- Chrome、Chromium 或 Edge

  Chrome, Chromium, or Edge.
- 首次安装 Python 依赖时可联网

  Network access for the initial Python dependency installation.

## 安装提示 / Installation Notice

> 麻烦请先阅读 [安全须知](安全须知.md)，再阅读 [使用教程](使用教程.md)；使用教程中包含了具体的安装方式。
>
> Please read the [Safety Instructions](Safety%20Instructions.md) first, followed by the [User Guide](User%20Guide.md), which contains the detailed installation methods.

## 核心能力 / Core Capabilities

- CDP/DOM：读取页面、定位元素、Unicode 输入、标签页生命周期与 JavaScript 对话框

  CDP/DOM: page reading, element location, Unicode input, tab lifecycle, and JavaScript dialogs.
- 专用 Profile：从外部 Mem 配置读取回环端口并核验浏览器实际 Profile

  Dedicated profile: reads the loopback port from external Mem configuration and verifies the browser's actual profile.
- 桌面工具：在 DOM 无法覆盖的原生界面中截图、定位、鼠标和键盘操作

  Desktop tools: screenshots, positioning, mouse, and keyboard operations for native interfaces outside DOM coverage.
- 外部 Mem：只保存经过验证的可复用经验，并与浏览器 Profile 隔离

  External Mem: stores only verified reusable experience and remains isolated from the browser profile.
- 安全边界：认证阶段禁止截图，不记录秘密，不自动绕过 CAPTCHA/MFA，不盲目重试高影响动作

  Safety boundaries: no screenshots during authentication, no secret recording, no automated CAPTCHA/MFA bypass, and no blind retry of high-impact actions.

## 重要说明 / Important Notice

WebMind 提供**用户自己浏览器模式、Agent 专用浏览器模式和不可见模式**，默认使用不可见模式下的 Agent 专用 CDP 浏览器。

WebMind offers three modes: **user's own browser mode, dedicated Agent browser mode, and invisible mode**. By default, it uses the dedicated Agent CDP browser in invisible mode.

> [!IMPORTANT]
> **首次登录建议先使用可见模式。** 专用 CDP 浏览器使用与日常浏览器隔离的独立 Profile，可保存登录状态等浏览器数据。首次创建的 Profile 不包含你在日常浏览器中已有的登录状态。建议在安装并初始化 Mem 后，或首次执行需要登录的网站任务前，以可见模式（`--visible-mode`）打开专用浏览器，并由你本人完成所需网站的登录。
>
> **Use visible mode for the first sign-in.** The dedicated CDP browser uses a separate profile from your everyday browser and can retain sign-in state and other browser data. A newly created profile does not inherit your everyday browser's sign-in state. After installing WebMind and initializing Mem, or before the first task on a site that requires sign-in, open the dedicated browser in visible mode (`--visible-mode`) and sign in to the required sites yourself.

登录状态通常会保留在同一个 Mem 绑定的 Profile 中。在登录状态仍有效时，后续任务一般无需每次先打开可见模式登录，可直接使用不可见模式；首次登录新网站或登录状态失效时，再使用可见模式完成登录。

Sign-in state usually persists in the profile bound to the same Mem. While it remains valid, later tasks can generally run in invisible mode without a visible sign-in step each time. Use visible mode again when signing in to a new site or when an existing session is no longer valid.

**请先在本机安装 Google Chrome，再执行浏览器任务。** 专用 CDP 浏览器由本机已安装的 Chrome 启动，并使用独立 Profile；WebMind 不包含 Chrome 本体。

**Install Google Chrome on your computer before running browser tasks.** The dedicated CDP browser runs using your locally installed Chrome with a separate profile; WebMind does not bundle Chrome.

## 每次任务的浏览器模式 / Browser Mode per Task

专用 CDP 浏览器默认使用不可见模式，不显示窗口。用户可为当前任务选择可见模式（`--visible-mode`）；模式参数仅控制新浏览器启动。已有浏览器会告知实际模式及 ESC 停止提示后继续复用，不因模式不同报错。不可见模式通过 CDP 操作，不能用桌面鼠标键盘直接操作隐藏页面；需要人工登录或接管时应暂停并切换到可见模式。具体命令见[使用教程](使用教程.md#42-每次任务前选择是否使用不可见模式)。

The dedicated CDP browser defaults to invisible mode without a visible window.
Users may choose visible mode for the current task with `--visible-mode`; previous
launch choices are not saved. An existing verified browser keeps its actual mode;
the Agent announces it with the ESC stop notice before continuing. Invisible pages use CDP,
not desktop mouse/keyboard input.
Pause for a transition to visible mode when manual authentication or takeover is needed.
See the [User Guide](User%20Guide.md#42-choose-invisible-mode-for-each-task).

## 隐私与本机数据 / Privacy and Local Data

源码仓库不包含活动 Mem、已登录 Profile、位置指针、Cookie、截图、虚拟环境或安装元数据。`.gitignore` 会拦截常见的本地凭据和运行数据，但提交前仍应人工检查 `git status`。

The source repository contains no active Mem, signed-in profile, location pointer, cookies, screenshots, virtual environment, or installation metadata. `.gitignore` blocks common local credentials and runtime data, but `git status` should still be reviewed manually before committing.

默认运行环境位于 `%LOCALAPPDATA%\WebMindCodex`；默认 Skill 位于 `$HOME\.agents\skills\webmind-codex`。这两个路径按当前用户动态解析，不绑定某个用户名、盘符或电脑。

The default runtime environment is `%LOCALAPPDATA%\WebMindCodex`, and the default Skill location is `$HOME\.agents\skills\webmind-codex`. Both paths are resolved dynamically for the current user and are not tied to a username, drive letter, or computer.

## 项目结构 / Project Structure

- `SKILL.md`：Skill 入口和工作流约束

  `SKILL.md`: Skill entry point and workflow constraints.
- `agents/openai.yaml`、`assets/`：Codex 展示元数据

  `agents/openai.yaml`, `assets/`: Codex display metadata.
- `scripts/`：安装器、统一启动器和运行时检查

  `scripts/`: installer, unified launcher, and runtime checks.
- `components/`：CDP、截图、鼠标、键盘、等待和 Mem 六个组件

  `components/`: six components for CDP, screenshots, mouse, keyboard, waits, and Mem.
- `使用教程.md`、`安全须知.md`：中文用户文档

  `使用教程.md`, `安全须知.md`: Chinese user documentation.
- `User Guide.md`、`Safety Instructions.md`：英文用户文档

  `User Guide.md`, `Safety Instructions.md`: English user documentation.
- `references/`：安装和官方来源说明

  `references/`: installation and official-source references.

## 参与贡献与安全问题 / Contributing and Security

提交改动前请阅读 [CONTRIBUTING.md](CONTRIBUTING.md)。安全漏洞请按 [SECURITY.md](SECURITY.md) 私下报告，不要在公开 Issue 中披露敏感细节。

Read [CONTRIBUTING.md](CONTRIBUTING.md) before submitting changes. Report vulnerabilities privately according to [SECURITY.md](SECURITY.md), without disclosing sensitive details in public issues.

## 许可证 / License

本项目采用 [MIT License](LICENSE)。

This project is licensed under the [MIT License](LICENSE).

## 项目成员

- 开发者（Developer）：Zhengdao Li
- 指导者（Supervisor）：Mingyue Cheng
