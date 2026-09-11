> Component reference for the `webuse-codex` skill. Read the root `SKILL.md` first.
> `$WebUseRoot` (PowerShell) / `$WEBUSE_ROOT` (bash) is the absolute directory
> containing that root SKILL.md; derive it from the discovered skill path.
> These variables are assigned by the agent, not supplied by Codex.
> Use the root launchers so installation paths and UTF-8 are handled consistently.

# webuse-cdp

Use this skill when Codex can operate a Chrome page more reliably through CDP than through visual mouse/keyboard automation.

## Cross-platform launcher

Commands below use `webuse` as shorthand. Do not invoke a command named
`webuse` directly. Use the plugin launcher for the current OS:

```powershell
# Windows PowerShell
& "$WebUseRoot\scripts\webuse.ps1" cdp <command> [options]
```

```bash
# macOS
bash "$WEBUSE_ROOT/scripts/webuse.sh" cdp <command> [options]
```

For every example written as `webuse cdp ...`, translate it to the matching
launcher above. If dependencies are missing, run `scripts/install.ps1` on
Windows or `scripts/install.sh` on macOS from the project root.

## Scope

CDP is best for browser-internal work:

- list and select Chrome tabs
- navigate pages
- evaluate JavaScript in the page
- read DOM state and page metadata
- wait for CSS selectors
- move the CDP pointer without clicking and inspect its position in screenshots
- click, fill, or focus elements by selector
- dispatch key events
- capture page screenshots
- accept or dismiss JavaScript alert/confirm/prompt dialogs

CDP cannot reliably control native OS windows, browser permission bubbles, file pickers, extension popups, save dialogs, or other UI outside the page DOM.

## Popup rule

When using CDP, if a native browser, OS, permission, file picker, extension, download, save, or other visible popup blocks progress, Codex may independently use other WebUse skills to handle it:

1. Use `webuse-screenshot` to inspect the visible popup.
2. Use `webuse-mouse-control` to move and click after screenshot confirmation.
3. Use `webuse-typing` only when keyboard focus and input method are safe.
4. Use `webuse-wait` for short wait-and-inspect loops.
5. Return to CDP after the popup is cleared.

For JavaScript alert/confirm/prompt dialogs, prefer CDP's dialog handling first.

## Program

Run the bundled Python program:

```bash
webuse cdp <command> [options]
```

Browser control uses only the Python standard library. Screenshots with the
CDP pointer marker require Pillow 10.1 or newer:

Install all project dependencies once with `scripts/install.ps1` on Windows or
`scripts/install.sh` on macOS.

`screenshot --no-cursor` retains the original screenshot behavior and needs no
external Python packages.

The script defaults to a persistent CDP-only browser profile in writable user data:

```text
Windows: %LOCALAPPDATA%\WebUseCodex\chrome-profile
macOS:   ~/Library/Application Support/WebUseCodex/chrome-profile
```

Do not ask the user for a profile path during normal use. Reuse this default profile so login state, cookies, and site preferences persist across days. Override it only when the user explicitly asks for a different CDP profile.

The default debugging endpoint is local-only:

```text
http://127.0.0.1:9223
```

The script launches Chrome with local binding and loopback proxy bypass:

```text
--remote-debugging-address=127.0.0.1
--remote-debugging-port=9223
--proxy-bypass-list=<-loopback>;localhost;127.0.0.1;::1
```

The Python CDP HTTP client also bypasses configured system/environment proxies for the CDP endpoint. This keeps CDP control local even when the user has a global network proxy enabled. Page traffic still follows Chrome/system proxy settings unless Chrome is configured otherwise.

Override the endpoint only when needed:

```bash
webuse cdp --endpoint http://127.0.0.1:9223 tabs --json
```

## Launch and Connection Behavior

### 打开浏览器前的告知（不阻塞任务）

每次准备打开浏览器前，Agent 必须先通过用户可见的进度消息（commentary）说明本次使用的浏览器类型，按实际情况只发送其中一句：

- 使用本 skill 的 Agent 专用 CDP profile：`本次打开的是CDP（Agent专用）Chrome。`
- 当前任务明确使用系统日常 Chrome profile，并通过相应方式打开普通 Chrome：`本次打开的是系统默认的Chrome。`

默认 CDP 启动使用第一句。使用系统安装的 Chrome 可执行文件不等于使用系统日常 profile；应按实际使用的 profile 区分。不要把两种类型或斜杠一起输出，也不要为了使用第二句而切换浏览器。若实际选用的是 Edge 等其它浏览器，应把名称改为真实浏览器名称。

这句话只是告知，绝不是确认问题或等待点。**不得仅因这句告知而请求确认、等待用户回复、调用用户输入工具、结束当前轮次或暂停原任务。发送后必须在同一轮立即调用打开浏览器的工具，并继续原任务。** 仅打印到脚本日志或在打开后补说不能替代打开前的用户可见告知。

该要求也覆盖自动启动：调用 `launch` 或任何启用了 auto-launch 的命令前，都先发送告知，因为这些命令可能打开浏览器。已经核实并连接到正确浏览器后，后续命令可使用 `--no-auto-launch` 复用，避免每次操作都重复告知；连接丢失需要重新打开时，先再次告知，再启动并继续任务。只读 `self-check` 不会启动浏览器，无需发送打开告知。

该告知不改变已有的 profile 校验与任务授权要求。

### Launch commands

For normal CDP work, send the opening notice above before commands that may launch Chrome. If the local endpoint is down, commands that need a tab automatically launch the fixed CDP browser profile first:

```bash
webuse cdp tabs --json
webuse cdp navigate --url "https://example.com" --wait-load --json
```

To explicitly start or reuse the fixed CDP browser:

```bash
webuse cdp launch --json
webuse cdp launch --url "https://www.zhihu.com" --json
```

Use `--no-auto-launch` for subsequent operations on an already verified browser,
or when checking an existing endpoint without starting Chrome. If it is no
longer available and the task needs it, send the opening notice before relaunching
and continue the task without waiting for a reply to that notice.

Every command verifies that the connected browser's explicit `--user-data-dir`
matches the selected profile before accessing page targets. This also applies
to `--no-auto-launch` and to a newly launched browser once its endpoint is ready.
If the profile differs or cannot be verified, stop using that endpoint. Do not
treat a responding port, tab title, or URL as proof of the correct profile.
Use an unused debugging port or a user-requested profile instead; do not close
the other browser automatically.

Verification uses the browser's reported command-line arguments. Windows can
also verify an existing browser without `--enable-automation`. On POSIX,
structured arguments require `--enable-automation`, which this launcher adds;
existing browsers without it cannot be verified. Relative or ambiguous profile
arguments are rejected rather than resolved against this script's working directory.

Use `--chrome-path` or the `WEBUSE_CDP_CHROME` environment variable only if Chrome/Edge is not found automatically. Use `--user-data-dir` or `WEBUSE_CDP_PROFILE` only when the user asks for a non-default CDP profile.

## Target selection

Most commands operate on one page tab. Select the target with one of:

```bash
--target-id <tab-id>
--url-contains <text>
--title-contains <text>
```

If no target is provided, the script selects the first page tab from `/json/list`.

## Commands

### Check endpoint

```bash
webuse cdp self-check --json
```

Reports whether the endpoint responds, the selected profile can be verified,
and page targets are available. `expected_profile` is the requested directory;
`profile` is populated only after verification succeeds, with
`profile_verified: true`. Failed verification returns `ok: false`,
`profile: null`, and a nonzero exit status without launching Chrome.

### Launch Fixed Browser

```bash
webuse cdp launch --json
```

Starts the persistent CDP-only browser profile when the endpoint is unavailable.
If the endpoint already responds, reuse is allowed only after verifying its
profile. A successful response reports the verified actual `profile` and
`profile_verified: true`; a mismatch or unverifiable browser is an error.

### List tabs

```bash
webuse cdp tabs --json
```

Returns tab IDs, titles, URLs, target types, and WebSocket availability.

### Navigate

```bash
webuse cdp navigate --url "https://example.com" --wait-load --json
```

Use `--wait-load` when the next step depends on page load completing.
Use `--url-stdin` instead of `--url` when a non-sensitive URL should not appear
in process arguments. Never pass secrets, session tokens, or authentication
links through either form.

If CDP returns a non-empty `Page.navigate.errorText`, navigation failed even if
the protocol request itself received a response. The CLI reports `ok: false`,
includes the CDP error text, skips the load wait, and exits nonzero.

### Evaluate JavaScript

```bash
webuse cdp eval --expression "document.title" --json
```

Use this to inspect DOM state, extract text, or run page-side helpers. Avoid executing destructive JavaScript unless the user requested that effect.

### Wait For Selector

```bash
webuse cdp wait-for-selector --selector "main" --visible --timeout 10 --json
```

Use this instead of fixed waits when a DOM condition is available.

### Move the CDP Pointer

```bash
webuse cdp --no-auto-launch move --target-id <tab-id> --selector "button[type=submit]" --json
webuse cdp --no-auto-launch move --target-id <tab-id> --x 240 --y 160 --json
```

Moves the CDP pointer without clicking. Use either a selector or both coordinates.
Coordinates are CSS pixels relative to the page viewport, not desktop or PNG
pixels. Non-finite or out-of-viewport coordinates are rejected.

For a visual check before clicking, move to the intended selector, capture the
same `--target-id`, inspect the marker and page, then continue with the intended
action. A move can trigger the page's normal hover behavior.

### Click Selector

```bash
webuse cdp click --selector "button[type=submit]" --json
```

The script scrolls the element into view, computes its center point, and dispatches
CDP mouse events. Its mouse movement also updates the CDP pointer position used
by subsequent screenshots of the same document.

### Fill Selector

```bash
webuse cdp fill --selector "input[name=q]" --text "search terms" --json
```

The script sets input-like values and dispatches `input` and `change` events. For contenteditable elements, it replaces text content.
Use `--text-stdin` for non-sensitive content that should not appear in process
arguments. The result never echoes the inserted value. Do not use this command
for passwords, one-time codes, tokens, payment data, or other critical private
values; pause for direct user entry.

### Insert Text

```bash
webuse cdp insert-text --selector "textarea" --text "hello" --json
```

This focuses the selector and uses `Input.insertText`, which is closer to user typing than directly setting `.value`.
It also supports `--text-stdin` with the same privacy restrictions as `fill`.

### Press Key

```bash
webuse cdp press --key Enter --json
```

Use after focusing the intended element.

### Screenshot

```bash
webuse cdp screenshot --output page.png --json
```

Captures the visible page viewport through CDP.

By default, the PNG includes an arrow with a blue `CDP` label at the last position
successfully sent by this script's `move` or `click` command. The marker is
composited into the returned PNG; it does not insert elements into the page.
It represents the Agent's last CDP operation position, not the system's physical
mouse pointer. Other clients, direct raw CDP calls, and physical mouse movement
do not update this marker.

The position is kept separately for each tab's current document and survives
CLI reconnects. Navigation or reload that replaces the document clears it.
If there is no known position, it is outside the viewport, or the pointer/viewport
changes during capture, the screenshot is returned without a marker and with
an explicit warning. Never infer a pointer position from such an image.

Use `move` first when a pointer position needs to be established:

```bash
webuse cdp --no-auto-launch move --target-id <tab-id> --selector "button[type=submit]" --json
webuse cdp --no-auto-launch screenshot --target-id <tab-id> --output page.png --json
```

To obtain an unannotated screenshot:

```bash
webuse cdp screenshot --no-cursor --output page.png --json
```

The JSON `cursor` field reports `source: "cdp"` and `drawn`. When drawn, it also
includes the CSS coordinates `x`/`y`, `coordinate_space: "viewport-css-pixels"`,
`kind: "operation-marker"`, and `image_point` in output PNG pixels. When omitted,
`reason` explains why. Inspect `warnings` as well as `ok`; a successful screenshot
does not necessarily contain a pointer. This marker cannot confirm OS mouse
placement for `webuse-mouse-control` actions.

### Handle JavaScript Dialog

```bash
webuse cdp handle-js-dialog --accept --timeout 3 --json
webuse cdp handle-js-dialog --dismiss --timeout 3 --json
```

Use only for JavaScript dialogs. For native popups, follow the popup rule and use the visual WebUse skills.

## Safety

- Prefer CDP for DOM-readable pages and WebUse visual skills for native or visual-only surfaces.
- Verify the target tab with `tabs` before actions that may submit data, purchase, delete, send, or publish.
- Use `wait-for-selector` after navigation or page changes.
- If a selector does not identify the intended element, inspect with `eval` or use screenshots before proceeding.
