# 参与贡献

感谢你改进 WebMind for Codex — Windows。

## 开始前

1. 先阅读 `SKILL.md`、`使用教程.md`、`安全须知.md` 和相关组件的 `GUIDE.md`。
2. 保留 CDP、截图、鼠标、键盘、等待和外部 Mem 六个组件。
3. 不得删除 Profile 核验、初始化门禁、隐私规则或 PyAutoGUI failsafe。
4. 不要提交活动 Mem、浏览器 Profile、位置指针、Cookie、截图、凭据、安装元数据或本机绝对路径。

## 提交改动

- 保持文本为 UTF-8（无 BOM）和 LF 换行。
- Python 保持兼容 3.10 及以上版本。
- 若更改命令行行为，同步更新根教程和对应组件指南。
- 若增加依赖，同时更新根 `requirements.txt` 和相关组件的依赖声明。
- PR 应说明变更目的、风险、验证方式和未验证的原生 Windows 行为。

发布前至少运行：

```powershell
python -B .\scripts\install.py --dry-run
& '.\scripts\webmind.ps1' doctor --json
```

`doctor` 不会启动浏览器。真实浏览器或桌面验证只能使用非敏感页面、临时账号和外部测试 Mem；不得把生成的数据提交到仓库。

## 报告问题

普通缺陷和功能建议可以使用 GitHub Issue。安全漏洞请遵循 [SECURITY.md](SECURITY.md)，不要公开披露利用细节或真实用户数据。
