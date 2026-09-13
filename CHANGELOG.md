# Changelog

本项目的重要变更记录在此文件中，版本号遵循 [Semantic Versioning](https://semver.org/)。

## [9.9.9] - 2026-09-13

### Changed

- 整理 macOS / Claude Code 独立发行结构和公开安装说明。
- 增加发布前隐私保护、贡献指南、安全报告流程和 GitHub 模板。
- 在安装依赖前检查 Python 版本。
- 将 marketplace 标识调整为适合公开分发的名称。
- 将 Mem 派生的 CDP 端口改为 `9000 + yyy`（9001-9999），并为完全匹配旧规则的 schema-1 Profile 元数据提供显式初始化迁移。

### Removed

- 移除内部测试源码、测试报告、验证产物和源文件交付记录。
