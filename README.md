> 提示：切换 branch 可以切换不同操作系统版本，包括 macOS 或 Windows 下的 Claude Code 版和 Codex 版。
>
> Tip: Switch branches to change between the Claude Code and Codex editions for macOS or Windows.
>
> 你现在看到的是 macOS 下的 Claude Code 版，版本号 MC 1.0.0。
>
> You are viewing the Claude Code edition for macOS, version MC 1.0.0.

# WebMind for Claude Code（macOS）

WebMind 是一个面向 Claude Code 的本地插件，为 macOS 提供 CDP/DOM 浏览器控制、桌面截图、鼠标键盘操作、有界等待，以及与浏览器 Profile 隔离的外部记忆（Mem）。

WebMind is a local Claude Code plugin for macOS that provides CDP/DOM browser control, desktop screenshots, mouse and keyboard operations, bounded waits, and external memory (Mem) isolated from the browser profile.

> 本项目只能在具有可见桌面会话的原生 macOS 上运行。它会操作网页和桌面，请在安装前阅读[安全须知](安全须知.md)。
>
> This project runs only on native macOS with a visible desktop session. It operates webpages and the desktop, so read the [Safety Instructions](Safety%20Instructions.md) before installation.

## 功能 / Features

- 优先通过 CDP/DOM 读取和操作网页，并校验专用浏览器 Profile。

  Prefer CDP/DOM for reading and operating webpages, with dedicated browser-profile verification.
- 新建、切换和安全关闭标签页。

  Create, switch, and safely close tabs.
- 在必要时截图并操作鼠标、键盘，支持 Retina 坐标换算。

  Capture screenshots and operate the mouse and keyboard when necessary, with Retina coordinate conversion.
- 将可复用经验保存到插件目录之外的 Mem；浏览器 Profile 不参与检索。

  Store reusable experience in Mem outside the plugin directory; browser profiles are excluded from retrieval.
- 对发送、发布、删除、付款、上传和敏感信息设置明确的安全边界。

  Enforce explicit safety boundaries for sending, publishing, deleting, paying, uploading, and sensitive information.

## 环境要求 / Requirements

- macOS（Apple Silicon 或 Intel）

  macOS on Apple Silicon or Intel.
- Python 3.10 或更高版本

  Python 3.10 or later.
- 最新版 Claude Code

  The latest Claude Code release.
- Chrome、Chromium 或 Edge

  Chrome, Chromium, or Edge.
- 首次安装 Python 依赖时可访问网络

  Network access for the initial Python dependency installation.

## 安装提示 / Installation Notice

> 麻烦请先阅读 [安全须知](安全须知.md)，再阅读 [使用教程](使用教程.md)；使用教程中包含了具体的安装方式。
>
> Please read the [Safety Instructions](Safety%20Instructions.md) first, followed by the [User Guide](User%20Guide.md), which contains the detailed installation methods.

默认安装：把完整发行版解压到桌面后，可以直接告诉 Claude Code“帮我安装这个 WebMind”。Agent 应按[安装流程](references/INSTALLATION.md)运行安装器，将完整插件复制到 `~/.claude/skills/webmind-claudecode`，再准备依赖。用户无需另选长期目录；新会话核验通过后，桌面下载副本可自行删除。不要把桌面目录注册成默认 marketplace 来源，也不要手动写入插件缓存。

Default installation: extract the complete distribution to the desktop and ask Claude Code to install it. Follow the [installation workflow](references/INSTALLATION.md): the installer copies the whole plugin into `~/.claude/skills/webmind-claudecode` and prepares dependencies. No separate permanent folder is needed. After verification in a new session, the downloaded copy may be removed by the user. Do not register the desktop source as the default marketplace or write plugin caches manually.

`CLAUDE_CONFIG_DIR` changes the Claude configuration root; installation and subsequent Claude sessions must use the same value. File copying and dependency diagnostics do not prove that Claude loaded the plugin: verify its six skills and actual root after restarting in a new conversation.

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

## 数据与隐私 / Data and Privacy

仓库不应包含真实 Mem、浏览器 Profile、登录状态、账号凭据、截图或本机位置指针。运行时产生的 `skills/webmind-mem/mem-location.json`、虚拟环境和常见敏感配置文件已加入 `.gitignore`。公开发布前仍应检查 Git 暂存区，避免把本地生成内容加入提交。

The repository must not contain real Mem, browser profiles, sign-in state, account credentials, screenshots, or local location pointers. Runtime `skills/webmind-mem/mem-location.json`, virtual environments, and common sensitive configuration files are listed in `.gitignore`. Check the Git staging area before publishing to avoid committing locally generated content.

## 项目结构 / Project Structure

- `.claude-plugin/`：Claude Code 插件与 marketplace 元数据。

  `.claude-plugin/`: Claude Code plugin and marketplace metadata.
- `scripts/`：安装器、统一入口和共享运行时代码。

  `scripts/`: installer, unified entry point, and shared runtime code.
- `skills/`：CDP、Mem、截图、鼠标、键盘和等待能力。

  `skills/`: CDP, Mem, screenshot, mouse, keyboard, and wait capabilities.
- `使用教程.md`、`安全须知.md`：中文安装、使用和风险说明。

  `使用教程.md`, `安全须知.md`: Chinese installation, usage, and risk documentation.
- `User Guide.md`、`Safety Instructions.md`：对应的完整英文版本。

  `User Guide.md`, `Safety Instructions.md`: corresponding complete English documentation.
- `references/`：宿主集成资料。

  `references/`: host integration references.

## 参与贡献与安全问题 / Contributing and Security

提交改动前请阅读 [CONTRIBUTING.md](CONTRIBUTING.md)。安全漏洞请按 [SECURITY.md](SECURITY.md) 私下报告，不要在公开 Issue 中附带凭据、Profile、日志或截图。

Read [CONTRIBUTING.md](CONTRIBUTING.md) before submitting changes. Report vulnerabilities privately according to [SECURITY.md](SECURITY.md), without attaching credentials, profiles, logs, or screenshots to public issues.

## 许可证 / License

本项目采用 [MIT License](LICENSE)。

This project is licensed under the [MIT License](LICENSE).

## 项目成员

- 开发者（Developer）：Zhengdao Li
- 指导者（Supervisor）：Mingyue Cheng
