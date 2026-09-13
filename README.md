> 提示：切换 branch 可以切换不同操作系统版本，包括 macOS 或 Windows 下的 Claude Code 版和 Codex 版。
>
> Tip: Switch branches to change between the Claude Code and Codex editions for macOS or Windows.
>
> 你现在看到的是 macOS 下的 Claude Code 版，版本号 MC 1.0。
>
> You are viewing the Claude Code edition for macOS, version MC 1.0.

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