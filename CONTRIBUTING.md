# Contributing

感谢你改进 WebMind for Codex。提交变更前，请先阅读 `SKILL.md`、`安全须知.md` 和与改动有关的组件 `GUIDE.md`。

## 开发原则

- 保留 CDP、截图、鼠标、键盘、Mem 和等待六个组件的完整协作关系。
- 不削弱 Profile 归属校验、回环地址限制、敏感输入限制、用户授权边界或 PyAutoGUI failsafe。
- 不提交真实 Mem、浏览器 Profile、Cookie、登录状态、截图、安装元数据、位置指针、日志或账号信息。
- 所有文本文件使用 UTF-8（无 BOM）与 LF；Python 代码支持 3.10 及以上版本。
- 新增依赖时同步更新根目录及相关组件的依赖声明，并说明必要性。

## 提交前检查

在 macOS 或 POSIX shell 中运行：

```bash
bash "./scripts/install.sh" --dry-run
python3 -m compileall -q scripts components
bash -n scripts/install.sh scripts/webmind.sh components/webmind-cdp/scripts/launch_chrome_macos.sh
```

涉及真实浏览器或桌面的变更，只能在目标 macOS 设备上使用一次性测试 Profile 验证。不要用日常 Profile，也不要把验收产生的数据提交到仓库。

## Pull Request

PR 请说明变更目的、风险边界、验证方式和文档影响。安全漏洞不要提交公开 Issue 或公开 PR，请按 `SECURITY.md` 报告。
