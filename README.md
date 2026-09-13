> 提示：切换 branch 可以切换不同操作系统版本，包括 macOS 或 Windows 下的 Claude Code 版和 Codex 版。
>
> Tip: Switch branches to change between the Claude Code and Codex editions for macOS or Windows.
>
> 你现在看到的是 Windows 下的 Claude Code 版，版本号 WC 1.0。
>
> You are viewing the Claude Code edition for Windows, version WC 1.0.

# WebMind Windows / Claude Code

面向 **Windows + Claude Code** 的本地浏览器与桌面自动化插件。项目提供 CDP / DOM 网页控制、截图、鼠标、键盘、有界等待和外部 Mem；不包含浏览器、登录资料、账号凭据或用户数据。

A local browser and desktop automation plugin for **Windows + Claude Code**. It provides CDP/DOM web control, screenshots, mouse and keyboard input, bounded waits, and external Mem; it does not include a browser, sign-in data, account credentials, or user data.

> [!WARNING]
> 本插件能够改变网页、账号和桌面状态。使用前请完整阅读[使用教程](使用教程.md)和[安全须知](安全须知.md)；英文版见 [User Guide](USER_GUIDE.md) 和 [Safety Instructions](SAFETY_INSTRUCTIONS.md)。请从低风险任务开始。不要公开上传 Mem、浏览器 Profile、Cookie、截图或 `mem-location.json`。
>
> This plugin can change webpages, accounts, and desktop state. Read the [User Guide](USER_GUIDE.md) and [Safety Instructions](SAFETY_INSTRUCTIONS.md) in full before use. Start with low-risk tasks, and never publish Mem, browser profiles, cookies, screenshots, or `mem-location.json`.

## 环境要求 / Requirements

- Windows 10/11，使用可见的本机桌面会话

  Windows 10/11 with a visible local desktop session.
- Claude Code

  Claude Code.
- Python 3.10 或更高版本

  Python 3.10 or later.
- Chrome、Chromium 或 Edge

  Chrome, Chromium, or Edge.
- 首次安装 Python 依赖时需要联网

  Network access for the initial Python dependency installation.

## 安装提示 / Installation Notice

> 麻烦请先阅读 [安全须知](安全须知.md)，再阅读 [使用教程](使用教程.md)；使用教程中包含了具体的安装方式。
>
> Please read the [Safety Instructions](SAFETY_INSTRUCTIONS.md) first, followed by the [User Guide](USER_GUIDE.md), which contains the detailed installation methods.

## 数据边界 / Data Boundaries

- Python 虚拟环境默认位于 `%LOCALAPPDATA%\WebMind\.venv`，可用 `WEBMIND_DATA_DIR` 改变位置。

  The Python virtual environment defaults to `%LOCALAPPDATA%\WebMind\.venv`; use `WEBMIND_DATA_DIR` to change its location.
- 活动 Mem 必须位于插件目录之外；浏览器 Profile 保存在对应 Mem 内。

  Active Mem must stay outside the plugin directory; the browser profile is stored inside its corresponding Mem.
- 仓库只会保存被忽略的 Mem 位置指针 `skills/webmind-mem/mem-location.json`，不应提交任何运行时数据。

  The repository stores only the ignored Mem location pointer at `skills/webmind-mem/mem-location.json`; no runtime data should be committed.
- CDP 调试地址仅允许本机回环接口；不要转发或公开调试端口。

  CDP debugging is restricted to local loopback interfaces; never forward or expose the debugging port.

## 项目结构 / Project Structure

- `.claude-plugin/`：插件与 marketplace 清单

  `.claude-plugin/`: plugin and marketplace manifests.
- `scripts/`：安装器、统一入口和共享运行时代码

  `scripts/`: installer, unified entry point, and shared runtime code.
- `skills/`：六个 Claude Code Skills 及其实现

  `skills/`: six Claude Code Skills and their implementations.
- `使用教程.md`、`安全须知.md`：中文用户文档

  `使用教程.md`, `安全须知.md`: Chinese user documentation.
- `USER_GUIDE.md`、`SAFETY_INSTRUCTIONS.md`：英文用户文档

  `USER_GUIDE.md`, `SAFETY_INSTRUCTIONS.md`: English user documentation.
- `references/`：宿主集成参考资料

  `references/`: host integration references.

## 参与和安全报告 / Contributing and Security Reports

提交改进前请阅读 [CONTRIBUTING.md](CONTRIBUTING.md)。安全漏洞请按 [SECURITY.md](SECURITY.md) 的方式报告，不要在公开 Issue 中包含凭据、Profile、截图或其他敏感数据。

Read [CONTRIBUTING.md](CONTRIBUTING.md) before submitting improvements. Report vulnerabilities according to [SECURITY.md](SECURITY.md), and never include credentials, profiles, screenshots, or other sensitive data in public issues.

## 许可证 / License

[MIT License](LICENSE)

This project is licensed under the [MIT License](LICENSE).
