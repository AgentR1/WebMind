# Claude Code 官方参考

以下宿主集成资料于 2026-09-13 核对。项目源码定义 WebMind 的具体行为；这些链接只用于说明 Claude Code 的插件加载、分发和权限机制。

1. [创建插件](https://code.claude.com/docs/en/plugins)
2. [插件 Marketplace](https://code.claude.com/docs/en/plugin-marketplaces)
3. [插件技术参考](https://code.claude.com/docs/en/plugins-reference)
4. [CLI 参考](https://code.claude.com/docs/en/cli-usage)
5. [权限配置](https://code.claude.com/docs/en/permissions)

Installation references checked on 2026-10-06:

- [Plugins in the personal skills directory](https://code.claude.com/docs/en/plugins/create#make-a-plugin-load-in-every-session)
- [Plugin origins, in-place loading and name conflicts](https://code.claude.com/docs/en/plugins/loading)
- [Local marketplace source behavior](https://code.claude.com/docs/en/plugin-marketplaces#test-an-edit-to-a-plugin)

Local compatibility check: Claude Code 2.1.289 recognized a complete Windows plugin copy under an isolated `CLAUDE_CONFIG_DIR/skills/webmind-claudecode` as `webmind-claudecode@skills-dir`. Both edition manifests validated. This records a tested release, not a minimum version or a native macOS/session-loading guarantee.
