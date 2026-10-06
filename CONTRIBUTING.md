# 参与贡献

感谢你改进 WebMind。提交 Issue 或 Pull Request 前，请先确认内容不包含账号凭据、Cookie、浏览器 Profile、真实 Mem、私人截图、绝对用户路径或其他个人信息。

## 开发环境

本项目的运行目标是原生 macOS。准备 Python 3.10 或更高版本、Claude Code，以及 Chrome、Chromium 或 Edge，然后运行：

```bash
bash ./scripts/install.sh --deps-only
bash ./scripts/webmind.sh doctor --json
```

## 提交改动

- 每个 Pull Request 聚焦一个主题，并说明行为变化与人工验证范围。
- 保持 Python、Shell、Markdown 和 JSON 文件为 UTF-8、LF 换行。
- 不要削弱风险确认、浏览器归属校验、回环地址限制或敏感信息保护。
- 涉及真实网页或桌面时，只使用无敏感数据的测试页面和专用 Profile。
- 用户可见变更应更新 README、使用教程或 CHANGELOG。

不可见模式回归检查（不启动真实浏览器或访问用户 Profile）：

```text
python -B -m unittest discover -s tests -v
```

## 报告安全问题

不要通过公开 Issue 披露可利用细节。请按照 [SECURITY.md](SECURITY.md) 的流程私下报告。

安装器回归使用仓库内 `.tmp-install-test-*` 临时目录，不调用 pip、不修改真实 Claude 配置或用户 Mem；测试完整复制、更新保留、失败回退和移走下载源后的诊断。发布前还应在对应原生系统的新 Claude 会话中核验实际插件根和六个 Skill，静态测试不能代替这一验证。
