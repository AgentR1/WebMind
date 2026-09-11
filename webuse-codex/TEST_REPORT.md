# Validation report

Build: WebUse for Codex 2.0.0. Validation date: 2026-09-09.

## Scope and results

| Check | Result |
| --- | --- |
| Original source unit baseline | 69 collected: 66 passed, 3 Windows-specific skips |
| Modified project's code-only suite | 103 collected: 100 passed, 3 Windows-specific skips; no failures/errors |
| Suite with opt-in browser tests | 105 collected: 101 passed, 4 skips; no failures/errors |
| Root Codex skill validator | Passed |
| Python source syntax and UTF-8/LF checks | Passed |
| Bash wrapper syntax and help/dry-run smoke checks | Passed |
| Actual copied install, custom runtime, spaces/Chinese paths and Chinese memory write | Passed as part of adapter tests |
| Windows/macOS actual desktop operation | **Not executed** |
| PowerShell execution/parsing on Windows | **Not executed here**; native CI and local checklist provided |
| Native CI matrix | Supplied, **not executed** in this delivery |

The execution host was Linux (Debian), Python 3.13.5, not Windows or macOS. The
original three skipped tests require Windows command-line parsing/path semantics.
The new cross-platform branch tests use mocks and therefore are not substitutes
for actual Windows/macOS operation. Installing dependencies into native Mac/Win
Python environments, Codex session discovery, OS permission dialogs, focus,
Retina/mixed-DPI multi-monitor input and signed-in desktop access still require
local acceptance using `references/SMOKE_TEST.md`.

Machine-readable results are in `validation/unit-results.json` and
`validation/browser-results.json`. `passed` excludes skipped tests. Do not report
all 103 or all 105 tests as having passed.

## Live browser test boundaries

Chromium 144.0.7559.96 was used with a disposable headless profile, never a real
account. The live `about:blank` smoke test passed: CDP connection, endpoint profile
verification, JavaScript result, Chinese UTF-8 stdin and PNG screenshot export.
The remaining rendering/cursor lifecycle test **did not run to completion**:
this host's browser policy blocked its local HTTP fixture with an organizational
access-denied page. An initial attempt failed when the test looked for a selector
on that denial page. The fixture now detects the proven policy-denial page and
reports that test as skipped; no browser policy was changed and normal selector
or rendering failures remain failures.

The Linux container runs as root and required an external headless test wrapper
with root-container-only Chromium flags (including `--no-sandbox`). That wrapper
is **not shipped**, is not used by the project installer or runtime, and must not
be copied into a user's normal desktop setup. This test says nothing about Codex
sandbox approval or real Windows/macOS accessibility permissions.

## Coverage added for the port

The adapter suite covers recorded path persistence and upgrade retention, env
precedence, real-copy installation and backup locations, existing-folder refusal,
AGENTS preservation/idempotence, UTF-8 input including BOM and multiline text,
script-path resolution outside the source cwd, native-host/WSL guards, private
Windows desktop rejection, independent Mac capture/input permissions, logical
Retina coordinates and negative origins, loopback-only binding, user-local Mac
browser discovery, bounded waits and exactly one discoverable Codex skill.

The original component tests continue to exercise WebSocket frame buffering,
fragmentation, UTF-8, ownership verification, cursor composition, navigation
errors, mouse/keyboard behavior, memory and screenshots. Core test assertions
were retained; the screenshot test fixture now writes a real synthetic PNG to
support the new image-scale metadata.

## Reproduce

From an extracted source copy with requirements installed:

```text
python -B scripts/run_tests.py
python -B scripts/run_tests.py --browser
```

The second command uses only a disposable profile and generated loopback test
content. It must not be substituted for the separate native desktop checklist.
The project itself does not grant OS permissions, change Codex sandbox settings,
relax browser policies, or automatically activate the bundled generic memory template.
