# WebMind macOS / Claude Code: setup

Read the complete local [User Guide](../User%20Guide.md) and [Safety Instructions](../Safety%20Instructions.md). Chinese versions are also bundled as [使用教程](../使用教程.md) and [安全须知](../安全须知.md).
Use the platform launcher contained in this edition. Do not install only a component.
The source folder stores only a selected-Mem pointer; the user chooses external memory.

初始化成功后，按 [Mem 初始化要求](../skills/webmind-mem/SKILL.md) 主动向用户介绍用户自己浏览器模式、Agent 专用浏览器模式和不可见模式。不可见模式只能使用 Agent 专用浏览器，且为默认模式；用户可通过 `--visible-mode` 选择当前任务的可见模式，不继承上次选择。

After initialization succeeds, follow the [Mem initialization requirements](../skills/webmind-mem/SKILL.md)
and actively explain user's own browser mode, dedicated Agent browser mode and invisible
mode. Invisible mode is the default for the dedicated Agent browser. Use `--visible-mode`
when visible mode is requested for the current task; never inherit earlier choices.
