# webuse-mouse-control

Codex Skill for local mouse pointer control, clicking, and wheel scrolling.

Main file: `scripts/webuse_mouse_control.py`

See `GUIDE.md` for commands and usage guidance.


## Click and scroll safety rule

Before any click-style command (`left-click`, `right-click`, `left-down`, `left-up`, or `left-hold`) or the `scroll` command, Codex must first take a screenshot and visually confirm that the cursor is at the intended target. If the cursor is wrong, move it and screenshot again before clicking or scrolling.

## Scroll examples

```bash
webuse mouse scroll --direction up --amount 5 --json
webuse mouse scroll --direction down --amount 5 --json
webuse mouse scroll --x 500 --y 300 --direction down --amount 6 --json
```
