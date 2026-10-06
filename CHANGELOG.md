# Changelog

本项目的显著变更记录在此文件中，版本号遵循[语义化版本](https://semver.org/lang/zh-CN/)。

## [Unreleased]

- Claude Code 默认安装改为完整复制到个人 Skills 目录，无需用户准备长期来源目录；增加暂存安装、受管更新备份、保留目标 Mem 指针、来源冲突提示和六个 Skill 的加载核验，保留 `--deps-only` 兼容方式。

- 为 Windows Claude Code 版增加任务级不可见模式（`cdp --invisible-mode`）；未指定时默认使用不可见模式，新增互斥参数 `--visible-mode`，保留 `--invisible-mode`，不持久化上次选择。
- 识别浏览器实际模式；已有实例模式不符时告知实际模式及 ESC 停止提示，然后继续复用，并保留 Profile/端口校验。
- 同步中英文教程、安全须知与 Skills，说明不可见模式的 CDP 操作范围和人工接管流程。
- 初始化完成后必须主动介绍用户自己浏览器模式、Agent 专用浏览器模式及仅限专用浏览器的不可见模式；同步中英文初始化要求与教程。
- 在 global 初始规则模板中以中英文定义三种使用模式，明确不可见模式专指以 Chrome headless 模式运行 Agent 专用浏览器。

## [1.0.0] - 2026-09-13

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
