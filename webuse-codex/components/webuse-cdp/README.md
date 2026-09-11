# webuse-cdp

Component of the `webuse-codex` skill for controlling Chrome pages through the Chrome DevTools Protocol (CDP).

Main file: `scripts/webuse_cdp.py`

Before opening a browser, the Agent announces whether it is using the dedicated
CDP Chrome or the system's everyday Chrome, then immediately continues the task
without asking for confirmation or waiting for a reply. This includes automatic
launches and relaunches; see the opening-notice rule in [GUIDE.md](GUIDE.md).

## Fixed CDP browser

By default this skill uses one persistent CDP-only Chrome profile:

```text
Windows: %LOCALAPPDATA%\WebUseCodex\chrome-profile
macOS:   ~/Library/Application Support/WebUseCodex/chrome-profile
```

Do not ask the user for a profile path during normal Codex use. Reusing this directory keeps login state across days.

The launcher binds CDP to localhost and bypasses proxies for loopback addresses:

```text
--remote-debugging-address=127.0.0.1
--remote-debugging-port=9223
--proxy-bypass-list=<-loopback>;localhost;127.0.0.1;::1
```

The Python CDP client also connects to the local endpoint without using system or environment proxies.

## WebSocket transport

The bundled standard-library WebSocket client preserves bytes received after
the HTTP upgrade headers, buffers incomplete frames across timeouts, reassembles
fragmented text and binary messages, handles interleaved ping/pong and close
control frames, validates server frame structure and UTF-8 text, and limits a
message to 64 MiB. This is important for large CDP responses such as screenshot
payloads and for events that arrive while a command response is pending.

## Endpoint ownership

Before reusing a CDP endpoint, every browser command verifies the browser's
explicit `--user-data-dir` against the requested directory (the default above,
`--user-data-dir`, or `WEBUSE_CDP_PROFILE`). The same check runs after a new
browser starts. An open port or successful `/json/version` response alone is
not proof of ownership.

The check reads `Browser.getBrowserCommandLine` from the browser WebSocket.
On Windows, browsers without `--enable-automation` are also supported through
`SystemInfo.getInfo.commandLine`, parsed with Windows argument quoting rules.
On POSIX, the launcher adds `--enable-automation` to obtain structured arguments;
existing browsers need that flag too. The unstructured POSIX command line is
not used because it does not preserve argument boundaries reliably.

If the directory differs, or cannot be verified, the command fails without
operating page targets or launching another browser over the existing service.
Choose an unused debugging port, or explicitly select the intended data
directory. The script does not close another browser automatically.

Successful `launch` and `tabs` responses contain the verified actual `profile`
and `profile_verified: true`. `self-check` reports `expected_profile` separately;
when verification fails, `profile` is null and `profile_verified` is false.
Missing, relative, or ambiguous user-data directory arguments are rejected.

## Screenshot pointer

CDP screenshots now include a labelled arrow at the Agent's last `move` or
`click` position. Install the screenshot annotation dependency:

Use the project-level platform installer in `scripts/` to install dependencies.

After connecting to the verified browser, move without clicking and capture the
same tab:

```bash
webuse cdp --no-auto-launch move --target-id <tab-id> --selector "button[type=submit]" --json
webuse cdp --no-auto-launch screenshot --target-id <tab-id> --output page.png --json
```

`move --x 240 --y 160` also accepts viewport CSS coordinates. The marker is drawn
into the PNG with Pillow, without modifying page DOM. It represents the last
CDP operation, not the system mouse pointer. If no position is known for the
current document, the image remains unannotated and the response explains why.
Use `screenshot --no-cursor` for the original screenshot without annotation or
the Pillow dependency. Full behavior and JSON fields are documented in
[GUIDE.md](GUIDE.md).

## Tests

From this skill directory, run:

```bash
python -B -m unittest discover -s tests -v
```

These regression tests mock browser I/O and never launch or operate a real browser.

`tests/browser/test_cursor_browser.py` is a separate, opt-in headless Chrome
integration test using a disposable profile and local test pages. It is not run
by the command above. Current validation and environment limitations are documented in the project
root `TEST_REPORT.md`; do not infer native-desktop validation from portable tests.

## Commands

```bash
webuse cdp launch --json
webuse cdp self-check --json
webuse cdp tabs --json
webuse cdp eval --expression "document.title" --json
webuse cdp navigate --url "https://example.com" --json
webuse cdp wait-for-selector --selector "h1" --json
webuse cdp move --selector "button[type=submit]" --json
webuse cdp click --selector "button[type=submit]" --json
webuse cdp fill --selector "input[name=q]" --text "hello" --json
webuse cdp screenshot --output page.png --json
```

`navigate` treats a non-empty CDP `Page.navigate.errorText` as a failure:
the JSON response has `ok: false`, preserves the original CDP result, and the
process exits with status 1 instead of waiting for a load event that cannot occur.

## Notes

Use CDP for browser-internal operations. If a native browser, OS, permission, file picker, or extension popup appears, Codex may use `webuse-screenshot`, `webuse-mouse-control`, `webuse-typing`, or `webuse-wait` to inspect and click through that visible popup before returning to CDP.
