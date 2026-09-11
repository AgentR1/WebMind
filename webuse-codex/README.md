# WebUse for Codex

**Codex 版 | Windows + macOS | v2.0.0**

本版本由原 WebUse 项目独立复制并修改，保留 CDP、截图、鼠标、键盘、等待和外部记忆六类能力；原压缩包不作修改。

这是一个安装到本机 Codex 的完整 skill 项目，不再依赖 Claude Code 插件机制。它需要本机 Codex 具有执行 shell 命令的能力，不是让云端 Codex 远程控制电脑的服务。

> **验证范围：**已执行代码测试、安装回归和有限的无头 Chromium CDP 测试。**Windows / macOS 真实桌面的端到端测试尚未执行**；详见 [TEST_REPORT.md](TEST_REPORT.md) 和 [本机验收清单](references/SMOKE_TEST.md)。

## 快速安装

先在同一台电脑安装 Python 3.10+、Codex 和 Chrome / Chromium / Edge；解压后在 `webuse-codex` 目录运行。安装依赖需要联网。

### Windows（原生 PowerShell）

```powershell
& '.\scripts\install.ps1'
& "$HOME\.agents\skills\webuse-codex\scripts\webuse.ps1" doctor --json
```

若 PowerShell 脚本策略阻止执行，使用 Python 入口，无需更改系统安全策略：

```powershell
py -3 -B '.\scripts\install.py'
py -3 -B "$HOME\.agents\skills\webuse-codex\scripts\bootstrap.py" doctor --json
```

不要使用 WSL 的 Linux Python 操作 Windows 桌面。Codex 沙箱若使用私有桌面，需通过 Codex 对具体本机命令的授权机制访问用户桌面；本项目不会自动关闭沙箱。

### macOS（Terminal / zsh / bash）

```bash
bash './scripts/install.sh'
bash "$HOME/.agents/skills/webuse-codex/scripts/webuse.sh" doctor --json
```

在系统设置中给实际执行命令的 Terminal / IDE / Codex 应用授予 **屏幕录制**和 **辅助功能** 权限，然后重启该应用。Apple Silicon 和 Intel Mac 分别使用本机架构的 Python，不要跨机器复制虚拟环境。

### 在 Codex 中调用

安装后重新打开本机 Codex 会话，用 `/skills` 检查，或直接在任务中写：

```text
$webuse-codex 请帮我完成这个已授权的本机网页任务，先读取相关 Mem 经验，执行后核验结果并整理有用的记忆。
```

默认安装到 `~/.agents/skills/webuse-codex`，不修改全局 `AGENTS.md` 或 Codex 配置。可选 `--add-agent-rules` 会有界限地添加路由规则并备份原文件。记忆读写是 Codex 执行流程，不是后台 hook。

## 目录结构

```text
webuse-codex/
  SKILL.md                 # One Codex-discoverable skill entrypoint
  agents/openai.yaml       # Codex UI metadata and invocation policy
  AGENTS.md                # Repository guidance, optional installer integration
  scripts/                 # Installer, platform wrappers, dispatcher, diagnostics
  components/              # Six retained modules and their GUIDE.md references
  examples/Mem/            # Portable generic template, never automatically activated
  references/              # Setup, native smoke checklist, official sources
  tests/                   # Adapter and cross-platform regression tests
  TEST_REPORT.md
  CHANGELOG.md
```

## Runtime and data isolation

| Item | Windows | macOS |
| --- | --- | --- |
| Runtime | `%LOCALAPPDATA%\WebUseCodex` | `~/Library/Application Support/WebUseCodex` |
| Environment | `<runtime>/.venv/Scripts/python.exe` | `<runtime>/.venv/bin/python` |
| Profile | `<runtime>/chrome-profile` | `<runtime>/chrome-profile` |
| Memory | `<runtime>/Mem` | `<runtime>/Mem` |

The default CDP port is **9223**, separate from the original edition's 9222.
Use `--data-dir PATH` during installation to persist a different runtime location.
Upgrades preserve this recorded path unless explicitly overridden. The new
`WEBUSE_CODEX_DATA_DIR` environment variable has priority; legacy `WEBUSE_DATA_DIR`
remains compatible. Clear legacy overrides to keep the two editions separate.
Only source files are packaged: no virtual environment, logged-in profile,
personal runtime Mem, browser executable, API key, or credentials are included.
The bundled memory example contains only portable generic guidance. It is not
automatically activated or copied into the user's runtime memory.

## Components

| Command | Capability |
| --- | --- |
| `cdp` | Dedicated browser, verified profile, tabs, DOM/JS, navigation, input, screenshots |
| `screenshot` | Desktop regions, cursor marker, Retina-to-desktop scale metadata |
| `mouse` | Move, click, hold and scroll; negative display origins and failsafe |
| `typing` | ASCII typing and portable `primary` shortcuts; Unicode through CDP |
| `wait` | A single two-second wait followed by an explicit state check |
| `mem` | Selective external memory, search, guarded rewrite and reconciliation |
| `doctor` | Paths, dependencies, browser availability and host permission checks |

Use the full platform launcher rather than assuming a `webuse` executable exists.
For example, append `cdp --help` or `mem --help` to the launcher shown above.
Complex JavaScript, Chinese text and multiline updates accept `--input-file FILE`
through the unified launcher, avoiding legacy PowerShell quoting/encoding loss.

## Documentation and tests

[Setup and advanced options](references/SETUP.md) explains project-scoped installs,
permissions, sandbox approvals, Unicode input, upgrades and removal.
[Migration notes](CHANGELOG.md) list structural changes.
[Official Codex sources](references/SOURCES.md) document the integration target.

```bash
python -B scripts/run_tests.py
python -B scripts/run_tests.py --browser
```

The first command runs code-only tests. The second additionally starts a
disposable headless browser and serves generated fixtures only on loopback; it
does not use real accounts. Platform-mocked tests do not replace real-machine
GUI acceptance. The included CI workflow is supplied for future Windows/macOS
runs; it was not executed as part of this delivery.
