# WebMind for Codex（macOS）

WebMind 是一个面向原生 macOS 的 Codex Skill，可在用户授权范围内通过 CDP/DOM、截图、鼠标和键盘操作本机浏览器与桌面，并把经过核验的可复用经验保存到仓库外部的 Mem。

> [!IMPORTANT]
> 本项目只能操作与 Codex 位于同一台 Mac、同一可见桌面会话中的浏览器。它不是远程控制服务，也不会绕过 Codex 审批、macOS 隐私权限、登录验证或网站安全机制。

## 功能

- CDP / DOM 页面读取、输入和标签页管理
- macOS 桌面截图及 Retina 坐标换算
- 鼠标、键盘和有界等待后备能力
- 与独立浏览器 Profile 绑定的外部 Mem
- Profile 归属校验、回环地址限制和敏感数据保护

## 环境要求

- 原生 macOS 桌面会话
- Codex CLI、Codex 桌面版或支持本地 Skill 的 Codex 环境
- Python 3.10 或更高版本
- Chrome、Chromium 或 Edge
- 首次安装 Python 依赖时需要联网

## 快速安装

如果尚未安装 Codex CLI，可按 [OpenAI 官方 Codex CLI 文档](https://learn.chatgpt.com/docs/codex/cli) 在 macOS 中安装并登录：

```bash
curl -fsSL https://chatgpt.com/codex/install.sh | sh
codex
```

下载或克隆本仓库后，在完整仓库根目录运行：

```bash
cd "/path/to/webmind-codex"
bash "./scripts/install.sh"
bash "$HOME/.agents/skills/webmind-codex/scripts/webmind.sh" doctor --json
```

安装器默认把 Skill 复制到 `~/.agents/skills/webmind-codex`，把 Python 虚拟环境放到 `~/Library/Application Support/WebMindCodex/.venv`。Codex 通常会自动发现 Skill；若没有出现，请重新启动 Codex。之后可在任务中显式调用：

```text
$webmind-codex 请在我授权的范围内完成这个本机浏览器任务……
```

首次执行网页或桌面任务前，还必须阅读风险说明并由用户选择仓库外部的 Mem 位置。完整步骤、项目级安装和自定义数据目录见 [使用教程](使用教程.md)。

English documentation: [User Guide](User%20Guide.md) and [Safety Instructions](Safety%20Instructions.md).

## 数据与隐私

仓库不包含真实 Mem、浏览器 Profile、登录状态、Cookie、截图、位置指针或安装后的虚拟环境。这些运行时数据都应留在仓库外部；常见运行时路径已加入 `.gitignore`。公开发布或提交 Issue 前，请仍检查日志和截图是否含有账号、路径或页面隐私信息。

详细安全边界见 [安全说明](安全说明.md)，漏洞报告方式见 [SECURITY.md](SECURITY.md)。

## 项目结构

- `SKILL.md`：Skill 入口与执行约束
- `scripts/`：安装器、统一启动器和运行时
- `components/`：CDP、截图、鼠标、键盘、Mem 与等待组件
- `agents/openai.yaml`：Codex 界面元数据
- `使用教程.md`、`安全说明.md`：中文用户文档
- `User Guide.md`、`Safety Instructions.md`：英文用户文档
- `references/`：安装和官方参考来源

参与开发前请阅读 [CONTRIBUTING.md](CONTRIBUTING.md)。
