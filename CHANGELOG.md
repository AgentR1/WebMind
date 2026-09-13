# Changelog

本项目遵循 [Semantic Versioning](https://semver.org/)。

## 9.9.9 - 2026-09-13

- 为 GitHub 公开发布清理测试、内部验证结果和源压缩包溯源信息。
- 增加许可证、贡献指南、安全策略、Issue/PR 模板、依赖更新配置和发布前静态检查。
- 扩充忽略规则，防止活动 Mem、浏览器 Profile、安装元数据、密钥和截图被误提交。
- 修复 Windows CRLF 输入文件未规范化为 LF 的问题。
- 补全等待组件缺失的 PowerShell 启动示例，并修正文档链接。
- 将 Mem 派生的 CDP 端口从旧规则迁移到 `9000 + yyy`（9001-9999），并为完全匹配旧规则的 schema-1 Profile 元数据提供显式初始化迁移。

## Earlier changes

- 提供 Windows + Codex 独立版，保留 CDP、截图、鼠标、键盘、等待和外部 Mem 六个组件。
- 加入原生宿主检查、Profile/端口核验、外部 Mem 门禁和隐私保护规则。
