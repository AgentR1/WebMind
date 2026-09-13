> 提示：切换 branch 可以切换不同操作系统版本，包括 macOS 或 Windows 下的 Claude Code 版和 Codex 版。
>
> Tip: Switch branches to change between the Claude Code and Codex editions for macOS or Windows.
>
> 你现在看到的是 macOS 下的 Codex 版，版本号 MX 1.0。
>
> You are viewing the Codex edition for macOS, version MX 1.0.

# WebMind for Codex（macOS）

WebMind 是一个面向原生 macOS 的 Codex Skill，可在用户授权范围内通过 CDP/DOM、截图、鼠标和键盘操作本机浏览器与桌面，并把经过核验的可复用经验保存到仓库外部的 Mem。

WebMind is a Codex Skill for native macOS. Within the user's authorization, it operates the local browser and desktop through CDP/DOM, screenshots, mouse, and keyboard input, and stores verified reusable experience in Mem outside the repository.

> [!IMPORTANT]
> 本项目只能操作与 Codex 位于同一台 Mac、同一可见桌面会话中的浏览器。它不是远程控制服务，也不会绕过 Codex 审批、macOS 隐私权限、登录验证或网站安全机制。
>
> This project can operate only a browser on the same Mac and in the same visible desktop session as Codex. It is not a remote-control service and does not bypass Codex approvals, macOS privacy permissions, authentication, or website security mechanisms.

## 功能 / Features

- CDP / DOM 页面读取、输入和标签页管理

  CDP/DOM page reading, input, and tab management.
- macOS 桌面截图及 Retina 坐标换算

  macOS desktop screenshots and Retina coordinate conversion.
- 鼠标、键盘和有界等待后备能力

  Mouse, keyboard, and bounded-wait fallbacks.
- 与独立浏览器 Profile 绑定的外部 Mem

  External Mem bound to a dedicated browser profile.
- Profile 归属校验、回环地址限制和敏感数据保护

  Profile ownership verification, loopback restrictions, and sensitive-data protection.

## 环境要求 / Requirements

- 原生 macOS 桌面会话

  A native macOS desktop session.
- Codex CLI、Codex 桌面版或支持本地 Skill 的 Codex 环境

  Codex CLI, Codex desktop, or another Codex environment that supports local Skills.
- Python 3.10 或更高版本

  Python 3.10 or later.
- Chrome、Chromium 或 Edge

  Chrome, Chromium, or Edge.
- 首次安装 Python 依赖时需要联网

  Network access for the initial Python dependency installation.

## 安装提示 / Installation Notice

> 麻烦请先阅读 [安全须知](安全须知.md)，再阅读 [使用教程](使用教程.md)；使用教程中包含了具体的安装方式。
>
> Please read the [Safety Instructions](Safety%20Instructions.md) first, followed by the [User Guide](User%20Guide.md), which contains the detailed installation methods.

## 数据与隐私 / Data and Privacy

仓库不包含真实 Mem、浏览器 Profile、登录状态、Cookie、截图、位置指针或安装后的虚拟环境。这些运行时数据都应留在仓库外部；常见运行时路径已加入 `.gitignore`。公开发布或提交 Issue 前，请仍检查日志和截图是否含有账号、路径或页面隐私信息。

The repository contains no real Mem, browser profile, sign-in state, cookies, screenshots, location pointer, or installed virtual environment. Runtime data must remain outside the repository; common runtime paths are listed in `.gitignore`. Before publishing or filing an issue, still check logs and screenshots for account, path, or page-private information.

详细安全边界见 [安全须知](安全须知.md)，漏洞报告方式见 [SECURITY.md](SECURITY.md)。

See the [Safety Instructions](Safety%20Instructions.md) for detailed safety boundaries and [SECURITY.md](SECURITY.md) for vulnerability reporting.

## 项目结构 / Project Structure

- `SKILL.md`：Skill 入口与执行约束

  `SKILL.md`: Skill entry point and execution constraints.
- `scripts/`：安装器、统一启动器和运行时

  `scripts/`: installer, unified launcher, and runtime.
- `components/`：CDP、截图、鼠标、键盘、Mem 与等待组件

  `components/`: CDP, screenshot, mouse, keyboard, Mem, and wait components.
- `agents/openai.yaml`：Codex 界面元数据

  `agents/openai.yaml`: Codex interface metadata.
- `使用教程.md`、`安全须知.md`：中文用户文档

  `使用教程.md`, `安全须知.md`: Chinese user documentation.
- `User Guide.md`、`Safety Instructions.md`：英文用户文档

  `User Guide.md`, `Safety Instructions.md`: English user documentation.
- `references/`：安装和官方参考来源

  `references/`: installation and official references.

参与开发前请阅读 [CONTRIBUTING.md](CONTRIBUTING.md)。

Read [CONTRIBUTING.md](CONTRIBUTING.md) before contributing.
