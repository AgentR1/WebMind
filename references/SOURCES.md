# Host integration references

Checked for this edition on 2026-09-13. These official pages explain Claude Code
host integration; the WebMind implementation and safety boundaries are documented in
this repository.

1. Create plugins

   `https://code.claude.com/docs/en/plugins`

2. Plugin marketplaces

   `https://code.claude.com/docs/en/plugin-marketplaces`

3. Configure permissions

   `https://code.claude.com/docs/en/permissions`

Installation references checked on 2026-10-06:

- [Plugins in the personal skills directory](https://code.claude.com/docs/en/plugins/create#make-a-plugin-load-in-every-session)
- [Plugin origins, in-place loading and name conflicts](https://code.claude.com/docs/en/plugins/loading)
- [Local marketplace source behavior](https://code.claude.com/docs/en/plugin-marketplaces#test-an-edit-to-a-plugin)

Local compatibility check: Claude Code 2.1.289 recognized a complete Windows plugin copy under an isolated `CLAUDE_CONFIG_DIR/skills/webmind-claudecode` as `webmind-claudecode@skills-dir`. Both edition manifests validated. This records a tested release, not a minimum version or a native macOS/session-loading guarantee.
