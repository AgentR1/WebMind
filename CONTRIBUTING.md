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
4. 本地运行 `claude plugin validate .`、`python -m compileall -q scripts skills tests`、`python -B -m unittest discover -s tests -v` 和 `python scripts/webmind.py doctor --json`。不可见模式回归测试不会启动真实浏览器或访问用户 Profile。
5. 涉及外部状态变更、安全边界或安装流程时，同步更新教程与安全须知。

提交贡献即表示你同意按本项目的 MIT License 发布该贡献。

安装器回归使用仓库内 `.tmp-install-test-*` 临时目录，不调用 pip、不修改真实 Claude 配置或用户 Mem；测试完整复制、更新保留、失败回退和移走下载源后的诊断。发布前还应在对应原生系统的新 Claude 会话中核验实际插件根和六个 Skill，静态测试不能代替这一验证。
