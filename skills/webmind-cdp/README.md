> 提示：切换 branch 可以切换不同操作系统版本，包括 macOS 或 Windows 下的 Claude Code 版和 Codex 版。
>
> 你现在看到的是 Windows 下的 Claude Code 版，版本号 WC 1.0。

# webmind-cdp - Windows / Claude Code

Read [SKILL.md](SKILL.md) for commands and safety constraints.
The complete standalone [User Guide](../../USER_GUIDE.md) and
[Safety Instructions](../../SAFETY_INSTRUCTIONS.md) are bundled in this edition. Chinese versions are available as [使用教程](../../使用教程.md) and [安全须知](../../安全须知.md).
Implementation: `scripts/webmind_cdp.py`.

New dedicated Agent browsers default to invisible mode: `webmind cdp launch --json`.
Use `webmind cdp --visible-mode launch --json` to request a visible new browser. Existing
verified browsers keep their actual mode, even when it differs from the request. Relay
`browser_mode_notice` before page actions, then continue without another confirmation.
`--invisible-mode` remains supported; the two mode flags are mutually exclusive. See SKILL.md for mode checks and manual takeover.
