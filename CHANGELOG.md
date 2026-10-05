# Changelog

All notable changes to this project are documented in this file.

## [Unreleased]

### Changed

- 为 macOS Codex 版增加任务级不可见模式（`cdp --invisible-mode`）；未指定时默认使用不可见模式，新增互斥参数 `--visible-mode`，保留 `--invisible-mode`，不持久化上次选择。
- 识别浏览器实际模式；已有实例模式不符时告知实际模式及 ESC 停止提示，然后继续复用，并保留 Profile/端口校验。
- 同步中英文教程、安全须知与 Skills，说明不可见模式的 CDP 操作范围和人工接管流程。
- 初始化完成后必须主动介绍用户自己浏览器模式、Agent 专用浏览器模式及仅限专用浏览器的不可见模式；同步中英文初始化要求与教程。
- 在 global 初始规则模板中以中英文定义三种使用模式，明确不可见模式专指以 Chrome headless 模式运行 Agent 专用浏览器。

- Prepared the project for a public GitHub repository.
- Reworked the README and installation guidance for repository-based distribution.
- Replaced internal delivery provenance metadata with public project documentation.
- Added English User Guide and Safety Instructions while retaining the Chinese editions.
- Made first-use initialization explicitly state that both `xxx` and `yyy` must each be unique for every new Mem on the same Mac.
- Moved Mem-derived CDP ports to `9000 + yyy` (9001-9999) and added explicit initialization migration for exact legacy schema-1 profile metadata.

### Removed

- Removed bundled regression tests, generated validation results and delivery reports.

## [1.0.0] - 2026-09-13

### Added

- Native macOS launchers and runtime checks.
- CDP/DOM browser control with profile ownership verification and safe tab lifecycle.
- Screenshot, mouse, keyboard, bounded wait and external Mem components.
- User- and project-scoped Skill installation with external runtime data.

### Security

- Restricted CDP to loopback endpoints and Mem-bound browser profiles.
- Kept authentication secrets, browser profiles and active memory out of the package.
