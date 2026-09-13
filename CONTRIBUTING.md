# Contributing

感谢你改进 WebMind Windows / Claude Code。

## 提交 Issue 前

- 确认问题发生在原生 Windows、Python 3.10+ 和当前版本的 Claude Code。
- 先运行 `python scripts/webmind.py doctor --json`，但公开日志前必须删除用户名、绝对路径、Mem 名称及其他本机信息。
- 搜索现有 Issue，避免重复报告。
- 安全漏洞请按 [SECURITY.md](SECURITY.md) 私下报告。

## Pull Request

1. 从小而明确的改动开始，并说明用户可观察到的行为变化。
2. 不要提交 Mem、浏览器 Profile、Cookie、截图、令牌、账号信息或本机配置。
3. 保持文本为 UTF-8（无 BOM）和 LF；Python 代码使用四个空格缩进。
4. 本地运行 `claude plugin validate .`、`python -m compileall -q scripts skills` 和 `python scripts/webmind.py doctor --json`。
5. 涉及外部状态变更、安全边界或安装流程时，同步更新教程与安全须知。

提交贡献即表示你同意按本项目的 MIT License 发布该贡献。
