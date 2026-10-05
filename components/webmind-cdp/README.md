> 提示：切换 branch 可以切换不同操作系统版本，包括 macOS 或 Windows 下的 Claude Code 版和 Codex 版。
>
> 你现在看到的是 Windows 下的 Codex 版，版本号 WX 1.0.0。

# webmind-cdp - Windows / Codex

Read [GUIDE.md](GUIDE.md) for commands and safety constraints.
The complete standalone [User Guide](../../User%20Guide.md) and
[Safety Instructions](../../Safety%20Instructions.md) are bundled in this edition.
Implementation: `scripts/webmind_cdp.py`.

New dedicated Agent browsers default to invisible mode: `webmind cdp launch --json`.
Use `webmind cdp --visible-mode launch --json` to request a visible new browser. Existing
verified browsers keep their actual mode, even when it differs from the request. Relay
`browser_mode_notice` before page actions, then continue without another confirmation.
`--invisible-mode` remains supported; the two mode flags are mutually exclusive. See [GUIDE.md](GUIDE.md#task-browser-mode) for mode checks and manual takeover.
