# WebMind

**基于 Chrome DevTools Protocol 的独立浏览器 Skill，供 AI 编程助手使用。**

[English](README.md) · [Skill 指令](SKILL.md) · [命令参考](references/commands.md) · [阅读工作流](examples/reading-workflows.md)

WebMind 提供一个精简的 Python CLI，让宿主 Agent 读取和操作专用的 Chrome 或 Chromium 浏览器。行动选择与结果理解由宿主的大语言模型完成，WebMind 提供浏览器控制能力，不内置 AI 模型，也不依赖第三方 Python 包。

## 功能

- 复用持久化浏览器配置，保留独立的登录状态和 Cookie。
- 使用 `read-page` 读取正文、标题层级和链接，使用 JavaScript 定制 DOM 查询。
- 列出标签页、选择唯一页面目标，导航后返回明确状态。
- 等待选择器、点击元素、填写字段、插入文本和发送按键。
- 截取页面视口 PNG，处理 JavaScript 对话框。
- 通过 13 个命令输出 JSON，方便 Agent 调用。

## 环境要求

Python 3.10+、Git，以及 Chrome 或 Chromium。程序会搜索 macOS、Linux、Windows 的常见浏览器路径，也会搜索 Windows 上的 Edge；这些搜索路径不代表所有系统与浏览器组合都已实测。自动查找失败时，可通过 `WEBMIND_CHROME` 指定浏览器可执行文件。

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

## 配置

全局选项放在**子命令之前**，`--json` 放在命令末尾。

| 配置项 | 默认值 | 覆盖方式 |
| --- | --- | --- |
| CDP 端点 | `http://127.0.0.1:9222` | `--endpoint` |
| 浏览器可执行文件 | 搜索系统常见路径 | `--chrome-path` 或 `WEBMIND_CHROME` |
| 持久化配置目录 | Skill 内的 `chrome-profile/` | `--user-data-dir` 或 `WEBMIND_PROFILE` |
| 自动启动 | 标签页相关命令默认开启 | `--no-auto-launch` |

命令行路径优先于环境变量。专用配置目录独立于日常浏览器配置，会保存浏览器状态，请保持其内容私密。

```bash
python3 scripts/webmind.py --endpoint http://127.0.0.1:9334 launch --json
python3 scripts/webmind.py --endpoint http://127.0.0.1:9334 tabs --json
python3 scripts/webmind.py --endpoint http://127.0.0.1:9334 --no-auto-launch self-check --json
```

后续命令应使用相同端点。`9334` 只是 `9222` 被占用时可选的端口示例；同一配置目录切换端口前，应关闭对应专用浏览器，或通过 `--user-data-dir` 选择另一个配置目录。

WebMind 需要 HTTP CDP 发现接口 `/json/version` 和 `/json/list`。在日常浏览器中通过 `chrome://inspect/#remote-debugging` 开启远程调试，不一定会提供这些接口。本项目使用专用配置目录与 `launch` 命令建立连接。

启动器默认将调试服务绑定到本地回环地址。Python CDP 连接绕过系统和环境变量代理，网页流量仍遵循浏览器的网络配置。调试端点能够控制浏览器会话，应保持本地访问。

## 命令与边界

全部命令为 `self-check`、`tabs`、`launch`、`read-page`、`eval`、`navigate`、`wait-for-selector`、`click`、`fill`、`insert-text`、`press`、`screenshot`、`handle-js-dialog`。参数和结果字段见[命令参考](references/commands.md)。

- 优先从 `tabs` 中选择 `type: "page"` 的条目，并明确指定 `--target-id`。目标必须唯一匹配；多个匹配或非页面目标会被拒绝。
- 导航会报告 `loaded`、`same-document`、`dispatched`、`failed`、`download` 或 `timeout`。导航错误和等待超时返回 `ok: false`，进程以非零状态退出。加载事件仍不代表动态内容已就绪。
- 输入操作成功发出时报告 `status: "dispatched"`、`outcome_verified: false`。填写结果中的 `immediate_value_verified: true` 只校验即时字段值；应进一步读取 DOM、校验提示或页面状态，确认网页实际结果。
- `read-page` 对当前文档做启发式快照提取，可能漏读或选错区域，应检查提取方式和截断信息。它不提供 OCR，不穿透 iframe 或 Shadow DOM，也不绕过登录与访问限制。
- 截图范围是页面视口，不是整页长截图或桌面截图。
- 原生文件选择器、浏览器权限气泡、扩展界面和系统弹窗不在 CLI 能力范围内；需要时可使用宿主已有的 GUI 工具。本包不依赖其他 Skill。
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

这些受控测试检查正文提取、浏览器操作及失败场景，与公开网站上的端到端任务基准不同，不能据此推断通用网站任务成功率。

仓库提供可选的 [GitHub Actions 模板](examples/github-actions-checks.yml)，用于在 macOS、Linux、Windows 和 Python 3.10、3.12 上运行离线测试。启用时，使用具备工作流权限的 GitHub 账号或令牌，将模板复制到 `.github/workflows/checks.yml`。位于 `examples/` 时不会自动运行。

## 许可与来源

使用 [MIT License](LICENSE) 发布。

WebMind 源于 WebUse 工具集的 `webuse_cdp` 组件，在此基础上整理为可独立分发的 Skill。
