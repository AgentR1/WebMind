# WebMind for Codex — Windows

面向原生 Windows 桌面的 Codex Skill：通过经过 Profile 核验的 CDP/DOM 控制浏览器，并在必要时使用截图、鼠标、键盘、有界等待和外部 Mem。

> [!WARNING]
> 本项目可以改变网页、账号和桌面状态。安装前请完整阅读 [使用教程](使用教程.md) 与 [安全说明](安全说明.md)。不要跳过首次风险接受和外部 Mem 选择。
> English documentation: [User Guide](User%20Guide.md) and [Safety Instructions](Safety%20Instructions.md).

## 运行要求

- Windows 10/11 的本地可见桌面会话（不支持 WSL、云端容器或远程控制另一台电脑）
- Codex 桌面版、CLI 或 IDE 扩展
- Python 3.10 或更高版本
- Chrome、Chromium 或 Edge
- 首次安装 Python 依赖时可联网

## 安装

OpenAI 官方文档确认，个人级 Skill 的发现目录为 `$HOME/.agents/skills`，也可以让内置 `$skill-installer` 从其他仓库下载 Skill。详见 [Build skills](https://developers.openai.com/codex/skills)。

### 方法一：从 GitHub 安装

发布仓库后，复制仓库的 HTTPS URL，并把 URL 与下面的请求放在同一条 Codex 消息中：

```text
$skill-installer 请从我在这条消息中提供的 GitHub 仓库 URL 安装 webmind-codex
```

随后在原生 PowerShell 中安装运行依赖并诊断：

```powershell
& "$HOME\.agents\skills\webmind-codex\scripts\install.ps1"
& "$HOME\.agents\skills\webmind-codex\scripts\webmind.ps1" doctor --json
```

### 方法二：从源码手动安装

完整下载或克隆仓库，在仓库根目录运行：

```powershell
py -3 --version
& '.\scripts\install.ps1'
& "$HOME\.agents\skills\webmind-codex\scripts\webmind.ps1" doctor --json
```

如果 PowerShell 阻止脚本，不要降低执行策略；改用 Python 入口：

```powershell
py -3 -B '.\scripts\install.py'
py -3 -B "$HOME\.agents\skills\webmind-codex\scripts\bootstrap.py" doctor --json
```

安装完成后重新打开 Codex；用 `$webmind-codex` 显式调用。完整初始化与用法见 [使用教程](使用教程.md)。

## 核心能力

- CDP/DOM：读取页面、定位元素、Unicode 输入、标签页生命周期与 JavaScript 对话框
- 专用 Profile：从外部 Mem 配置读取回环端口并核验浏览器实际 Profile
- 桌面工具：在 DOM 无法覆盖的原生界面中截图、定位、鼠标和键盘操作
- 外部 Mem：只保存经过验证的可复用经验，并与浏览器 Profile 隔离
- 安全边界：认证阶段禁止截图，不记录秘密，不自动绕过 CAPTCHA/MFA，不盲目重试高影响动作

## 隐私与本机数据

源码仓库不包含活动 Mem、已登录 Profile、位置指针、Cookie、截图、虚拟环境或安装元数据。`.gitignore` 会拦截常见的本地凭据和运行数据，但提交前仍应人工检查 `git status`。

默认运行环境位于 `%LOCALAPPDATA%\WebMindCodex`；默认 Skill 位于 `$HOME\.agents\skills\webmind-codex`。这两个路径按当前用户动态解析，不绑定某个用户名、盘符或电脑。

## 项目结构

- `SKILL.md`：Skill 入口和工作流约束
- `agents/openai.yaml`、`assets/`：Codex 展示元数据
- `scripts/`：安装器、统一启动器和运行时检查
- `components/`：CDP、截图、鼠标、键盘、等待和 Mem 六个组件
- `使用教程.md`、`安全说明.md`：中文用户文档
- `User Guide.md`、`Safety Instructions.md`：英文用户文档
- `references/`：安装和官方来源说明

## 参与贡献与安全问题

提交改动前请阅读 [CONTRIBUTING.md](CONTRIBUTING.md)。安全漏洞请按 [SECURITY.md](SECURITY.md) 私下报告，不要在公开 Issue 中披露敏感细节。

## 许可证

本项目采用 [MIT License](LICENSE)。
