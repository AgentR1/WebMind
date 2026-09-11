# Migration notes - 2.0.0

Derived independently from the user-supplied `WebUse.zip`.
Source archive SHA-256: `ca9c5e354fa664721f8df0b83a3f2246e2857763e767bb04b0ef746b42ed80f2`.
The original archive is unchanged. This is a local Codex skill, not an official
OpenAI product, published marketplace plugin or cloud-to-desktop service.

## Codex integration

- Replace the host-specific plugin manifest and per-skill registration with one
  root `SKILL.md` and `agents/openai.yaml` using Codex's local discovery layout.
- Move original modules from `skills/` to `components/`; convert their entrypoints
  to lazy-loaded `GUIDE.md` references, retaining their Python implementation,
  regression tests and original capability descriptions.
- Add user/project installers, explicit optional AGENTS routing, conflict checks,
  real-copy installation, external backups and upgrade rollback for code copies.
- Add path-aware bootstrap and a metadata file created only at installation time.
  A custom runtime path survives new shells and later managed upgrades.
- Keep original six capabilities. Start/end memory is an agent workflow, not a
  guaranteed lifecycle hook. The bundled portable Mem template is not live memory.

## Windows and macOS adaptation

- Provide PowerShell and bash launchers with explicit Python discovery, UTF-8
  environment, exit-status propagation and paths that contain spaces/non-ASCII.
- Support native Windows Python and native Intel/Apple Silicon macOS Python.
  Reject cloud/Linux/WSL desktop execution at the unified entrypoint with a
  diagnostic rather than implying access to a different user's desktop.
- Add non-prompting Screen Recording/Accessibility checks and Windows private
  desktop detection. Keep sandbox approvals and OS permissions separate.
- Add Windows DPI setup and native display geometry; report Retina image scale
  and preserve negative monitor origins. Keep keyboard `primary` portable.
- Add `--input-file` for Unicode text/JS/memory without fragile shell interpolation;
  add CDP `eval --expression-stdin` and a one-cycle `wait` command.
- Use separate WebUseCodex runtime/profile/Mem and loopback port 9223, retaining
  profile-ownership checks and rejecting nonloopback debugging binds.
- Improve browser discovery for user-local macOS Applications directories.

## Verification and preservation

Original WebSocket framing, ownership checks, cursor compositing, typing,
mouse and memory tests remain. Add adapter, installation, upgrade, Unicode,
permission, Retina and package regression tests. A real-browser test fixture now
uses local HTTP rather than data URLs; a proven organizational URL-policy denial
is reported as a specific skip, not silently treated as successful rendering.
Add an independent live about:blank CDP smoke test.

See `TEST_REPORT.md` for actual results and unexecuted native checks. No desktop
permission, browser policy, security sandbox or firewall configuration is changed
by this project. No logged-in profile or machine-specific virtual environment is
shipped. The bundled Mem template contains only portable generic guidance and is
retained only as an example.
