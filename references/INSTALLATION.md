# 完整插件安装流程 / Complete plugin installation

## 给 Agent 的安装规则

用户把完整发行版放到桌面并说“帮我安装”时，按下面顺序执行。桌面目录是下载来源，默认运行位置是 `%USERPROFILE%\.claude\skills\webmind-claudecode`。无需询问用户另选长期目录，不把下载来源注册为 marketplace，不手工创建或修改 Claude 的插件缓存、`installed_plugins.json` 或 `known_marketplaces.json`。

1. 阅读本发行版的使用教程及安全须知。检查原生 Windows 10/11、原生 Python 3.10+、完整插件和六个 Skill。安装请求已授权常规完整复制与依赖准备；只有超出请求范围或宿主明确要求的额外访问才另行处理权限。
2. 从下载副本运行 `scripts\install.ps1`，默认将完整插件复制到 Claude 的个人 Skills 区域，并创建/更新独立依赖环境 `%LOCALAPPDATA%\WebMind\.venv`。`CLAUDE_CONFIG_DIR` 若已设置，则以该配置根下的 `skills/webmind-claudecode` 为目标；后续 Claude 会话必须使用相同设置。`WEBMIND_DATA_DIR` 只改变依赖环境，不选择 Mem，必须位于插件目录外。
3. 从安装器报告的 **目标 `plugin_root`** 运行对应的 `webmind` launcher 和 `doctor --json`，检查六个 `skills` 项、五个可执行组件和依赖。不得继续运行桌面副本来证明安装成功。`--dry-run` 只检查并展示计划，不创建目录；`--skip-deps` 只复制文件，不表示依赖或宿主加载完成。依赖准备失败时，目标程序不被替换；共享 `.venv` 可能需要重新准备。
4. 检查 `claude plugin list --json` 和宿主插件管理器中的同名来源。默认期待 `webmind-claudecode@skills-dir`。`--plugin-dir`、`CLAUDE_CODE_PLUGIN_DIRS` 或已启用的 marketplace WebMind 可能遮盖新副本。安装器只报告可能的冲突，不改宿主设置。Agent 应说明具体来源，并在当前安装授权内停用对应旧 WebMind、按实际 scope 处理；不得停用无关插件、清空配置或删除整个 marketplace。管理策略锁定、来源不明或权限不足时，说明阻碍。移除下一次启动中指向旧 WebMind 的参数/环境变量；其它插件的参数需保留。如果新副本曾被禁用，应只重新启用其 `@skills-dir` 项。
5. 报告程序与依赖位置、诊断结果、备份位置和未解决的加载问题。明确告知“初始化和安装不要在同一个对话框内进行。在安装后一定要重启Claude code再进行初始化。” 本会话不创建、选择或迁移 Mem，不接受 Mem 风险，不启动浏览器或发送桌面输入。
6. 重启后的新会话按 [Mem Skill 的前置核验](../skills/webmind-mem/SKILL.md#pre-initialization-checks) 检查宿主实际加载的六个 Skill，并调用 `/webmind-claudecode:webmind-mem`。实际 `SKILL.md` 的根目录和该副本 doctor 的 `plugin_root` 必须都等于目标目录。`host_loading_verified: false` 是安装器/doctor 的诚实状态：它们不能证明会话加载，不能因文件存在就宣称六个 Skill 已启用。
7. 若当前 Claude 不支持 Skills 目录插件加载，先建议更新 Claude Code；需要兼容方式时，只将已复制的目标目录作为本地 marketplace 注册并安装，再在新会话核验实际加载根目录（见教程 2.2）。不得回退到桌面来源，也不得编造最低支持版本。只有核验通过后才告诉用户桌面副本已不再参与运行，可以自行删除；安装器从不自动删除下载源。

## 更新与数据边界

首次从旧桌面或 marketplace 副本迁移时，先记录实际启用副本的 Mem 名称和路径；下载源的指针不会自动继承。新会话的正式初始化应重新选择原 Mem，保留其 Profile，不要任意新建另一个 Mem 来代替。

从新下载副本再次运行默认安装器。仅带有本安装器同平台归属标记 `.webmind-install.json` 的目标才可替换；未知目录、符号链接或 junction 会被拒绝。先暂存完整新副本并准备依赖，保留 **目标已有** `skills/webmind-mem/mem-location.json`；不采用下载源中的位置指针。旧程序备份位于 Claude 配置根下的 `webmind-install-backups`，不放在 `skills` 中，避免被宿主发现为重复插件。替换失败会尝试恢复旧副本。安装器不会读取、复制或删除指针指向的外部 Mem/Profile，也不会复制下载源中的 `.git`、`.venv`、Mem/Profile、截图、日志或常见凭据文件。

归属标记只是防止误覆盖的本机标记，并非文件真实性或完整性的证明。不要分发安装副本中的标记、Mem 指针或备份。更新后重新启动 Claude，在新会话重新核验，然后再继续使用原 Mem。

## Agent installation workflow

For a complete desktop download and a request to install, use the default full-copy installer above. The user does not need to choose a separate permanent source. Honor `CLAUDE_CONFIG_DIR` consistently across installation and later sessions; `WEBMIND_DATA_DIR` changes dependencies only and must stay outside the plugin.

Run diagnostics from the reported destination, then inspect plugin origins. Only the matching old WebMind origin may be disabled within the installation request; preserve unrelated settings and plugins. An inline or marketplace copy can shadow `@skills-dir`. The installer reports possible conflicts without changing host configuration. A file copy or passing doctor is not proof of host loading.

Require a restart and a NEW conversation before Mem initialization. Verify all six loaded skills, the actual loaded `SKILL.md` root, and that copy's `doctor.plugin_root` against the destination. If the installed Claude cannot load skills-directory plugins, update Claude or use the compatibility marketplace route with the copied destination. Never register the desktop source. Leave the download in place; only after new-session verification may the user remove it.

For a first migration from an active desktop or marketplace copy, record its verified Mem name and path and reselect that original external Mem during initialization in the new conversation. The download pointer is not automatically adopted.

Updates stage a full copy, prepare dependencies before replacement, preserve the destination Mem pointer and retain the previous plugin outside the discovery directory. Unknown targets and links are refused. No external Mem/Profile is migrated or deleted. Backups can contain private pointers; keep them private. Dependency preparation can change the shared virtual environment even if program replacement fails.

Host behavior: [personal skills-directory plugins](https://code.claude.com/docs/en/plugins/create#make-a-plugin-load-in-every-session), [origins and name conflicts](https://code.claude.com/docs/en/plugins/loading).
