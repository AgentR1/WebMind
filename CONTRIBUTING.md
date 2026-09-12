# 参与贡献

感谢你改进 WebMind。提交 Issue 或 Pull Request 前，请先确认内容不包含账号凭据、Cookie、浏览器 Profile、真实 Mem、私人截图、绝对用户路径或其他个人信息。

## 开发环境

本项目的运行目标是原生 macOS。准备 Python 3.10 或更高版本、Claude Code，以及 Chrome、Chromium 或 Edge，然后运行：

```bash
bash ./scripts/install.sh
bash ./scripts/webmind.sh doctor --json
```

## 提交改动

- 每个 Pull Request 聚焦一个主题，并说明行为变化与人工验证范围。
- 保持 Python、Shell、Markdown 和 JSON 文件为 UTF-8、LF 换行。
- 不要削弱风险确认、浏览器归属校验、回环地址限制或敏感信息保护。
- 涉及真实网页或桌面时，只使用无敏感数据的测试页面和专用 Profile。
- 用户可见变更应更新 README、使用教程或 CHANGELOG。

## 报告安全问题

不要通过公开 Issue 披露可利用细节。请按照 [SECURITY.md](SECURITY.md) 的流程私下报告。
