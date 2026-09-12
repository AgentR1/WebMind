# WebMind Windows / Claude Code

面向 **Windows + Claude Code** 的本地浏览器与桌面自动化插件。项目提供 CDP / DOM 网页控制、截图、鼠标、键盘、有界等待和外部 Mem；不包含浏览器、登录资料、账号凭据或用户数据。

> [!WARNING]
> 本插件能够改变网页、账号和桌面状态。使用前请完整阅读[使用教程](使用教程.md)和[安全说明](安全说明.md)；英文版见 [User Guide](USER_GUIDE.md) 和 [Safety Instructions](SAFETY_INSTRUCTIONS.md)。请从低风险任务开始。不要公开上传 Mem、浏览器 Profile、Cookie、截图或 `mem-location.json`。

## 环境要求

- Windows 10/11，使用可见的本机桌面会话
- Claude Code
- Python 3.10 或更高版本
- Chrome、Chromium 或 Edge
- 首次安装 Python 依赖时需要联网

## 快速开始

克隆仓库或下载 GitHub Release 并完整解压，然后在原生 PowerShell 中运行：

```powershell
$WebMindRoot = 'C:\Tools\windows-claudecode' # 替换为实际项目根目录
& "$WebMindRoot\scripts\install.ps1"
& "$WebMindRoot\scripts\webmind.ps1" doctor --json
claude --plugin-dir "$WebMindRoot"
```

如果系统策略阻止 `.ps1`，无需修改执行策略；请按[使用教程的 Python 备用步骤](使用教程.md#22-手动安装)操作。`--plugin-dir` 只在当前 Claude Code 会话加载插件。

发布到 GitHub 后，也可以从仓库内置 marketplace 安装：

```powershell
claude plugin marketplace add <GitHub用户名>/<仓库名>
claude plugin install webmind-claudecode@webmind-claudecode
```

尖括号内容必须替换为实际 GitHub 仓库。完整的初始化、外部 Mem 选择、浏览器启动与故障处理步骤见[使用教程](使用教程.md)。

## 数据边界

- Python 虚拟环境默认位于 `%LOCALAPPDATA%\WebMind\.venv`，可用 `WEBMIND_DATA_DIR` 改变位置。
- 活动 Mem 必须位于插件目录之外；浏览器 Profile 保存在对应 Mem 内。
- 仓库只会保存被忽略的 Mem 位置指针 `skills/webmind-mem/mem-location.json`，不应提交任何运行时数据。
- CDP 调试地址仅允许本机回环接口；不要转发或公开调试端口。

## 项目结构

- `.claude-plugin/`：插件与 marketplace 清单
- `scripts/`：安装器、统一入口和共享运行时代码
- `skills/`：六个 Claude Code Skills 及其实现
- `使用教程.md`、`安全说明.md`：中文用户文档
- `USER_GUIDE.md`、`SAFETY_INSTRUCTIONS.md`：英文用户文档
- `references/`：宿主集成参考资料

## 参与和安全报告

提交改进前请阅读 [CONTRIBUTING.md](CONTRIBUTING.md)。安全漏洞请按 [SECURITY.md](SECURITY.md) 的方式报告，不要在公开 Issue 中包含凭据、Profile、截图或其他敏感数据。

## 许可证

[MIT License](LICENSE)
