# WebMind for Claude Code（macOS）

WebMind 是一个面向 Claude Code 的本地插件，为 macOS 提供 CDP/DOM 浏览器控制、桌面截图、鼠标键盘操作、有界等待，以及与浏览器 Profile 隔离的外部记忆（Mem）。

> 本项目只能在具有可见桌面会话的原生 macOS 上运行。它会操作网页和桌面，请在安装前阅读[安全须知](安全须知.md)。

> English documentation: [User Guide](User%20Guide.md) · [Safety Instructions](Safety%20Instructions.md)

## 功能

- 优先通过 CDP/DOM 读取和操作网页，并校验专用浏览器 Profile。
- 新建、切换和安全关闭标签页。
- 在必要时截图并操作鼠标、键盘，支持 Retina 坐标换算。
- 将可复用经验保存到插件目录之外的 Mem；浏览器 Profile 不参与检索。
- 对发送、发布、删除、付款、上传和敏感信息设置明确的安全边界。

## 环境要求

- macOS（Apple Silicon 或 Intel）
- Python 3.10 或更高版本
- 最新版 Claude Code
- Chrome、Chromium 或 Edge
- 首次安装 Python 依赖时可访问网络

## 快速开始

从 GitHub Releases 下载并解压源码，或克隆仓库。克隆时请将 `OWNER` 替换为实际 GitHub 用户名或组织名：

```bash
git clone https://github.com/OWNER/mac-claudecode.git
cd mac-claudecode
python3 --version
bash ./scripts/install.sh
bash ./scripts/webmind.sh doctor --json
claude --plugin-dir "$PWD"
```

`--plugin-dir` 只为这一次 Claude Code 会话加载插件。持久安装方式、首次 Mem 初始化和权限设置请见[完整使用教程](使用教程.md)。

## 数据与隐私

仓库不应包含真实 Mem、浏览器 Profile、登录状态、账号凭据、截图或本机位置指针。运行时产生的 `skills/webmind-mem/mem-location.json`、虚拟环境和常见敏感配置文件已加入 `.gitignore`。公开发布前仍应检查 Git 暂存区，避免把本地生成内容加入提交。

## 项目结构

- `.claude-plugin/`：Claude Code 插件与 marketplace 元数据。
- `scripts/`：安装器、统一入口和共享运行时代码。
- `skills/`：CDP、Mem、截图、鼠标、键盘和等待能力。
- `使用教程.md`、`安全须知.md`：中文安装、使用和风险说明。
- `User Guide.md`、`Safety Instructions.md`：对应的完整英文版本。
- `references/`：宿主集成资料。

## 参与贡献与安全问题

提交改动前请阅读 [CONTRIBUTING.md](CONTRIBUTING.md)。安全漏洞请按 [SECURITY.md](SECURITY.md) 私下报告，不要在公开 Issue 中附带凭据、Profile、日志或截图。

## 许可证

本项目尚未声明开源许可证。在仓库所有者选择并添加 `LICENSE` 前，默认保留全部权利。
