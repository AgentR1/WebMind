# Changelog

本项目的重要变更记录在此文件中，版本号遵循 [Semantic Versioning](https://semver.org/)。

## [Unreleased]

- 为 macOS Claude Code 版增加任务级不可见模式（`cdp --invisible-mode`）；未指定时默认使用不可见模式，新增互斥参数 `--visible-mode`，保留 `--invisible-mode`，不持久化上次选择。
- 识别浏览器实际模式；已有实例模式不符时告知实际模式及 ESC 停止提示，然后继续复用，并保留 Profile/端口校验。
- 同步中英文教程、安全须知与 Skills，说明不可见模式的 CDP 操作范围和人工接管流程。
- 初始化完成后必须主动介绍用户自己浏览器模式、Agent 专用浏览器模式及仅限专用浏览器的不可见模式；同步中英文初始化要求与教程。
- 在 global 初始规则模板中以中英文定义三种使用模式，明确不可见模式专指以 Chrome headless 模式运行 Agent 专用浏览器。

## [1.0.0] - 2026-09-13

### Changed

- 整理 macOS / Claude Code 独立发行结构和公开安装说明。
- 增加发布前隐私保护、贡献指南、安全报告流程和 GitHub 模板。
- 在安装依赖前检查 Python 版本。
- 将 marketplace 标识调整为适合公开分发的名称。
- 将 Mem 派生的 CDP 端口改为 `9000 + yyy`（9001-9999），并为完全匹配旧规则的 schema-1 Profile 元数据提供显式初始化迁移。

### Removed

- 移除内部测试源码、测试报告、验证产物和源文件交付记录。
