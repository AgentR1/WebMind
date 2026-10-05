> 提示：切换 branch 可以切换不同操作系统版本，包括 macOS 或 Windows 下的 Claude Code 版和 Codex 版。
>
> Tip: Switch branches to change between the Claude Code and Codex editions for macOS or Windows.
>
> 你现在看到的是 Windows 下的 Claude Code 版，版本号 WC 1.0.0。
>
> You are viewing the Claude Code edition for Windows, version WC 1.0.0.

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

## 安装前必读重要说明 / Important Information Before Installation

### To 用户 / To Users

Claude Code 在执行安装时可能无法正确保存调用命令，因此请注意：

Claude Code may not correctly retain the invocation command during installation. Please note:

1. 在完成安装后，请先重启 Claude Code，再进行初始化。

   After installation is complete, restart Claude Code before initialization.

2. 初始化中出现“你刚刚安装不是使用的最推荐方式，是否使用最推荐的方式继续”属正常情况，可以选择继续，除非是你主动选择不把 Skill 安装在推荐区域内。

   During initialization, the message “Your previous installation did not use the recommended method. Would you like to continue using the recommended method?” is expected. You may choose to continue unless you deliberately chose not to install the Skill in the recommended area.

### To Agent / To Agents

1. 安装后必须要求用户重启或重载宿主，让 Skill 从 `~/.claude/plugins/cache/` 加载。

   After installation, require the user to restart or reload the host so that the Skill loads from `~/.claude/plugins/cache/`.

2. `$WebMindRoot` 必须取自 `installed_plugins.json` 中当前启用插件对应条目的 `installPath`。

   `$WebMindRoot` must come from the `installPath` of the currently enabled plugin's entry in `installed_plugins.json`.

3. 禁止使用 `--plugin-dir`，禁止从下载源目录运行。禁止把 Skill 头部的 `Base directory` 当作插件根，除非它已在缓存目录内；即使如此，插件根仍须以 `installPath` 为准。

   Do not use `--plugin-dir` or run from the downloaded source directory. Do not treat the Skill header's `Base directory` as the plugin root unless it is already inside the cache directory; even then, use `installPath` as the authoritative plugin root.

4. 建议进行验证：确认 `Base directory` 位于 `.claude/plugins/cache/` 下，且 `doctor --json` 的 `plugin_root` 与它所属的插件根目录一致，并与 `installPath` 一致。若 `Base directory` 指向 `skills/<skill-name>`，应向上两级确定所属插件根目录，再比较规范化路径。若出现任一不符，尝试检查并修正错误。

   Recommended verification: confirm that `Base directory` is under `.claude/plugins/cache/`, and that the `plugin_root` reported by `doctor --json` matches its containing plugin root and `installPath`. If `Base directory` points to `skills/<skill-name>`, go up two directory levels to identify the containing plugin root, then compare canonical paths. If any check fails, investigate and attempt to correct the error.

## 安装提示 / Installation Notice

> 麻烦请先阅读 [安全须知](安全须知.md)，再阅读 [使用教程](使用教程.md)；使用教程中包含了具体的安装方式。
>
> Please read the [Safety Instructions](SAFETY_INSTRUCTIONS.md) first, followed by the [User Guide](USER_GUIDE.md), which contains the detailed installation methods.

## 每次任务的浏览器模式 / Browser Mode per Task

专用 CDP 浏览器默认使用不可见模式，不显示窗口。用户可为当前任务选择可见模式（`--visible-mode`）；模式参数仅控制新浏览器启动。已有浏览器会告知实际模式及 ESC 停止提示后继续复用，不因模式不同报错。不可见模式通过 CDP 操作，不能用桌面鼠标键盘直接操作隐藏页面；需要人工登录或接管时应暂停并切换到可见模式。具体命令见[使用教程](使用教程.md#42-每次任务前选择是否使用不可见模式)。

The dedicated CDP browser defaults to invisible mode without a visible window.
Users may choose visible mode for the current task with `--visible-mode`; previous
launch choices are not saved. An existing verified browser keeps its actual mode;
the Agent announces it with the ESC stop notice before continuing. Invisible pages use CDP,
not desktop mouse/keyboard input.
Pause for a transition to visible mode when manual authentication or takeover is needed.
See the [User Guide](USER_GUIDE.md#42-choose-invisible-mode-for-each-task).

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

## 项目成员

- 开发者（Developer）：Zhengdao Li
- 指导者（Supervisor）：Mingyue Cheng
