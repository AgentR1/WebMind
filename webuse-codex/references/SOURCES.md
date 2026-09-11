# Official integration references

Checked on 2026-09-09. These references document host integration, not evidence
that this specific package has been tested on every operating system.

1. OpenAI, **Build skills**. Local discovery under `.agents/skills`, explicit and
   implicit invocation, and `agents/openai.yaml`.
   https://developers.openai.com/codex/skills/
   (redirects to https://learn.chatgpt.com/docs/build-skills)
2. OpenAI, **Windows sandbox**. Native PowerShell, isolated/private desktops and
   sandbox permission boundaries.
   https://developers.openai.com/codex/windows/
   (redirects to https://learn.chatgpt.com/docs/windows/windows-sandbox)
3. OpenAI, **Custom instructions with AGENTS.md**. Repository scope, CODEX_HOME,
   and AGENTS.override.md precedence.
   https://developers.openai.com/codex/guides/agents-md/
   (redirects to https://learn.chatgpt.com/docs/agent-configuration/agents-md)
4. OpenAI, **Sandbox**. Platform-native enforcement and narrowly scoped approvals.
   https://learn.chatgpt.com/docs/sandboxing

The project does not assume that a terminal command will automatically open an
image in the model's context; SKILL.md explicitly requests the available host
image-viewing tool after capture.
