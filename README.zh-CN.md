# WebMind

**统一浏览器控制、桌面交互和本地经验复用的完整 Skill 套件。**

[English](README.md) · [Skill 指令](SKILL.md) · [浏览器命令](references/commands.md) · [阅读工作流](examples/reading-workflows.md) · [完整工作流](examples/full-workflow.md)

WebMind 是面向 AI 编程助手的完整自动化 Skill 套件，通过单一 `$webmind` 入口调用。六个模块覆盖专用 Chrome / Chromium 浏览器、本地经验文件、截图、鼠标、键盘输入和等待。行动选择与结果理解由宿主的大语言模型完成，WebMind 提供指引和工具，不内置 AI 模型。

## 六个模块

| 模块 | 提供的能力 | 指引 |
| --- | --- | --- |
| Core | 13 个 CDP 命令：标签页、导航、正文读取、DOM 操作、视口截图和 JavaScript 对话框；持久化浏览器会话。 | [浏览器命令](references/commands.md) |
| Experience（Memory） | 初始化、检查、索引、搜索、读取和记录本地经验，支持全局与任务经验文件。 | [经验管理](references/memory.md) |
| Screenshot | 桌面分辨率、全屏、半屏和矩形区域截图。 | [截图](references/screenshot.md) |
| Mouse | 位置、移动、点击、拖动和滚轮操作。 | [鼠标](references/mouse.md) |
| Typing | ASCII 文本输入、单键、按住/释放与快捷键。 | [键盘](references/typing.md) |
| Wait | 针对界面、进程及其他就绪信号的短等待与检查循环。 | [等待](references/wait.md) |

普通网页任务优先使用 Core，原生界面或只能通过视觉识别的内容使用桌面工具。Experience 已提供经验文件管理；经验选择、适用性判断和结果验证仍由宿主 Agent 完成，尚无自动学习或自动验证经验的引擎。

## 环境要求

需要 Python 3.10+ 和 Git；Core 浏览器操作还需要 Chrome 或 Chromium。Core 和 Experience（Memory）只使用 Python 标准库，桌面工具的可选依赖见下文。程序会搜索 macOS、Linux、Windows 的常见浏览器路径，也会搜索 Windows 上的 Edge；这些搜索路径不代表所有系统与浏览器组合都已实测。自动查找失败时，可通过 `WEBMIND_CHROME` 指定浏览器可执行文件。

## 安装

根据宿主选择 Skill 目录。macOS / Linux 上安装到 Codex：

```bash
mkdir -p "$HOME/.codex/skills"
git clone https://github.com/AgentR1/WebMind.git "$HOME/.codex/skills/webmind"
cd "$HOME/.codex/skills/webmind"
```

Claude Code 使用 `~/.claude/skills/webmind`：

```bash
mkdir -p "$HOME/.claude/skills"
git clone https://github.com/AgentR1/WebMind.git "$HOME/.claude/skills/webmind"
cd "$HOME/.claude/skills/webmind"
```

Windows PowerShell 上安装到 Codex：

```powershell
New-Item -ItemType Directory -Force "$HOME/.codex/skills" | Out-Null
git clone https://github.com/AgentR1/WebMind.git "$HOME/.codex/skills/webmind"
Set-Location "$HOME/.codex/skills/webmind"
```

PowerShell 下安装到 Claude Code 时，将上述命令中的 `.codex` 替换成 `.claude`。以下示例在安装后的 Skill 目录执行；Windows 安装 Python 3.10 或更新版本后，可用 `py -3` 替换 `python3`。

### 可选桌面依赖

需要桌面截图或输入控制时，在本地虚拟环境中安装 `mss`、Pillow 和 PyAutoGUI。macOS / Linux：

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-desktop.txt
.venv/bin/python scripts/webmind_screenshot.py self-check --json
```

Windows PowerShell：

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-desktop.txt
.\.venv\Scripts\python.exe scripts/webmind_screenshot.py self-check --json
```

截图、鼠标和键盘脚本应使用该虚拟环境的解释器。桌面操作还需要可交互的图形会话，以及操作系统要求的录屏或辅助功能权限。使用前阅读对应模块指引；安装依赖本身不代表已取得桌面访问能力。

## 快速开始

在宿主 Agent 中提出具体任务，例如：

> 使用 $webmind 打开 https://example.com，读取页面标题和正文。

也可以直接调用 CLI：

```bash
python3 scripts/webmind.py launch --json
python3 scripts/webmind.py tabs --json
```

从 `tabs` 输出中复制目标 `type: "page"` 条目的 `id`，替换下方 `TAB_ID`，再导航并读取页面：

```bash
python3 scripts/webmind.py navigate --target-id TAB_ID --url "https://example.com" --wait-load --json
python3 scripts/webmind.py read-page --target-id TAB_ID --wait-selector "h1" --max-chars 20000 --max-links 100 --json
python3 scripts/webmind.py screenshot --target-id TAB_ID --output page.png --json
```

`read-page` 返回页面标题、URL、语言、正文、标题层级、去重后的 HTTP(S) 链接，以及提取方式和截断信息。它通过启发式规则选择可能的正文区域；需要读取已观察到的特定区域时，使用 `--selector` 覆盖，定制 DOM 查询则使用 `eval`。登录态、动态内容和失败恢复示例见[阅读工作流](examples/reading-workflows.md)。

`launch` 会复用已响应的端点，只有新启动浏览器时才使用其 `--url` 参数。要在已有标签页中打开地址，请使用 `navigate`。本地端点不可用时，`tabs` 和标签页操作命令可自动启动专用浏览器；`self-check` 只检查端点。

具体网页任务开始前，按[经验管理指引](references/memory.md)选择相关经验；结果验证后，仅在宿主记忆权限允许时记录可复用的经验。经验是需要与当前页面核对的提示，不能作为发送、发布、购买或其他外部操作的授权。[完整工作流](examples/full-workflow.md)展示各模块如何配合。

## 配置

Core CLI 的全局选项放在**子命令之前**，`--json` 放在命令末尾。

| 配置项 | 默认值 | 覆盖方式 |
| --- | --- | --- |
| CDP 端点 | `http://127.0.0.1:9222` | `--endpoint` |
| 浏览器可执行文件 | 搜索系统常见路径 | `--chrome-path` 或 `WEBMIND_CHROME` |
| 持久化配置目录 | Skill 内的 `chrome-profile/` | `--user-data-dir` 或 `WEBMIND_PROFILE` |
| 自动启动 | 标签页相关命令默认开启 | `--no-auto-launch` |
| 经验目录 | `~/.local/share/webmind/Mem` | Memory CLI 的 `--mem-path` 或 `WEBMIND_MEM` |

命令行路径优先于环境变量。专用配置目录独立于日常浏览器配置，经验文件默认保存在 Skill 仓库之外。请勿将私人浏览器状态或个人经验提交到公共仓库；本仓库提供工具与示例，不包含个人记忆。

```bash
python3 scripts/webmind.py --endpoint http://127.0.0.1:9334 launch --json
python3 scripts/webmind.py --endpoint http://127.0.0.1:9334 tabs --json
python3 scripts/webmind.py --endpoint http://127.0.0.1:9334 --no-auto-launch self-check --json
```

后续命令应使用相同端点。`9334` 只是 `9222` 被占用时可选的端口示例；同一配置目录切换端口前，应关闭对应专用浏览器，或通过 `--user-data-dir` 选择另一个配置目录。

WebMind 需要 HTTP CDP 发现接口 `/json/version` 和 `/json/list`。在日常浏览器中通过 `chrome://inspect/#remote-debugging` 开启远程调试，不一定会提供这些接口。本项目使用专用配置目录与 `launch` 命令建立连接。

启动器默认将调试服务绑定到本地回环地址。Python CDP 连接绕过系统和环境变量代理，网页流量仍遵循浏览器的网络配置。调试端点能够控制浏览器会话，应保持本地访问。

## 命令与边界

Core 命令为 `self-check`、`tabs`、`launch`、`read-page`、`eval`、`navigate`、`wait-for-selector`、`click`、`fill`、`insert-text`、`press`、`screenshot`、`handle-js-dialog`。参数和结果字段见[浏览器命令参考](references/commands.md)，其他模块见上方各自指引。

- 优先从 `tabs` 中选择 `type: "page"` 的条目，并明确指定 `--target-id`。目标必须唯一匹配；多个匹配或非页面目标会被拒绝。
- 导航会报告 `loaded`、`same-document`、`dispatched`、`failed`、`download` 或 `timeout`。导航错误和等待超时返回 `ok: false`，进程以非零状态退出。加载事件仍不代表动态内容已就绪。
- 输入操作成功发出时报告 `status: "dispatched"`、`outcome_verified: false`。填写结果中的 `immediate_value_verified: true` 只校验即时字段值；应进一步读取 DOM、校验提示或页面状态，确认网页实际结果。
- `read-page` 对当前文档做启发式快照提取，可能漏读或选错区域，应检查提取方式和截断信息。它不提供 OCR，不穿透 iframe 或 Shadow DOM，也不绕过登录与访问限制。
- Core 截图范围是页面视口，Screenshot 模块则提供桌面和区域截图；两者均不自动生成完整网页长截图。
- 原生文件选择器、浏览器权限气泡、扩展界面和系统弹窗需要桌面交互。先观察桌面截图，再按 Mouse / Typing 指引或使用合适的宿主 GUI 工具操作，页面恢复可访问后返回 Core。
- 桌面鼠标使用主屏坐标，可能与截图或 DPI 缩放坐标不同。操作前确认映射与键盘焦点；网页非 ASCII 文本使用 Core `fill` 或 `insert-text`。
- 浏览器操作仍须符合用户的任务范围与宿主 Agent 的授权规则。

## 测试

在仓库根目录运行单元测试：

```bash
python3 -m unittest discover -s tests -v
```

浏览器集成测试需要显式启用，在真实 Chrome 中针对本地 HTTP 测试站点运行任务场景：

```bash
WEBMIND_TEST_CHROME=/absolute/path/to/chrome python3 -m unittest discover -s tests -v
```

PowerShell：

```powershell
$env:WEBMIND_TEST_CHROME = "C:\path\to\chrome.exe"
py -3 -m unittest discover -s tests -v
```

这些受控测试检查正文提取、浏览器操作及失败场景，与公开网站上的端到端任务基准不同，不能据此推断通用网站任务成功率。离线测试通过也不代表当前操作系统会话已有桌面权限，或鼠标、键盘已实测可用。

仓库提供可选的 [GitHub Actions 模板](examples/github-actions-checks.yml)，用于在 macOS、Linux、Windows 和 Python 3.10、3.12 上运行离线测试。启用时，使用具备工作流权限的 GitHub 账号或令牌，将模板复制到 `.github/workflows/checks.yml`。位于 `examples/` 时不会自动运行。

## 许可与来源

使用 [MIT License](LICENSE) 发布。

WebMind 源于整个 WebUse 工具集，包含浏览器、记忆、截图、鼠标、键盘与等待组件，在此基础上适配和扩展为统一分发的独立 Skill 套件。
