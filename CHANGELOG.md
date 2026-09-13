# Changelog

本项目的显著变更记录在此文件中，版本号遵循[语义化版本](https://semver.org/lang/zh-CN/)。

## [9.9.9] - 2026-09-13

### Added

- Windows 原生 Python 和 Claude Code 插件入口。
- CDP / DOM、截图、鼠标、键盘、有界等待和外部 Mem 六类能力。
- Mem 绑定的独立浏览器 Profile、动态回环端口和浏览器归属核验。
- 首次风险确认、外部 Mem 路径校验和敏感信息保护规则。

### Changed

- 整理公开发行文档、GitHub 社区文件和发布检查。
- 安装器明确校验 Python 3.10+，并兼容有或没有 Windows `py` 启动器的环境。
- 将 Mem 派生的 CDP 端口改为 `9000 + yyy`（9001-9999），并为完全匹配旧规则的 schema-1 Profile 元数据提供显式初始化迁移。

### Security

- 限制显式 CDP 调试地址为本机回环接口。
- 活动 Mem、浏览器 Profile 和位置指针不进入发行内容。
