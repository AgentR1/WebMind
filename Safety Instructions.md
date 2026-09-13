# WebMind Windows / Codex Safety Instructions

[Chinese version](%E5%AE%89%E5%85%A8%E9%A1%BB%E7%9F%A5.md)

Read these Safety Instructions carefully before using the WebMind Windows / Codex Skill.

The WebMind Windows / Codex Skill can perform real actions through browsers, desktop interfaces, mouse and keyboard input, CDP remote debugging, and related mechanisms. Because these operations can directly affect local files, account state, website data, and real-world business outcomes, the Skill's safety constraints cannot completely eliminate the risks of mistakes, malicious pages, software vulnerabilities, or other unforeseen conditions.

## 1. Safety constraints already included in the Skill

WebMind Windows / Codex includes multiple safety constraints intended to reduce the impact of sensitive-data exposure and unintended operations, including but not limited to the following:

1. **Do not take screenshots or save sensitive images during login or critical-data entry**

   During login, account recovery, MFA, verification-code, CAPTCHA, payment-authentication, and similar stages, screenshots are prohibited even when fields are empty or masked. Screenshots are also prohibited whenever critical private information is visible or being entered. This applies to full-screen, region, browser, CDP, and system screenshots. If an operation requires screenshot-based confirmation during such a stage, automation should pause and the user should complete the step.

2. **Do not write critical private information to Mem**

   WebMind Windows / Codex Mem is intended for reusable operational experience such as website entry points, page structure, stable selectors, and procedural steps.

   Passwords, verification codes, identity information, payment information, access tokens, cookies, private keys, and other sensitive credentials must not be stored in Mem.

3. **Stop automation when a sensitive step must be completed by the user**

   For password entry, verification codes, MFA, multi-factor authentication, CAPTCHA, payment confirmation, and other critical steps that must be completed or confirmed personally by the user, the Skill should stop automated interaction and hand control to the user rather than trying to bypass the security mechanism.

4. **Stop promptly after recognizing a consequential mistake may already have happened**

   If the Skill determines that it may have sent, deleted, submitted, uploaded, duplicated, or otherwise changed something incorrectly, it should prioritize stopping further actions that could continue changing external state and inform the user.

   In this situation, it should not retry, overwrite, undo, delete, or attempt to "repair" the result without user confirmation.

5. **Limit browser debugging exposure as much as possible**

   When CDP remote debugging is used, WebMind Windows / Codex is intended for local-machine use. Do not expose the remote-debugging port to the public Internet or an untrusted local network.

6. **Operate within the task scope explicitly given by the user**

   The Skill should stay within the user's requested goal. A browser already containing login state, permissions, or historical information does not authorize expansion of the operation scope.

## 2. Security risks that still remain

The constraints above can reduce risk but cannot guarantee absolute safety.

The following situations may still occur in real use:

1. **Incorrect operations can affect data or accounts**

   Changes in page structure, element-identification errors, misunderstanding of context, network latency, website faults, or other conditions can cause the Skill to click the wrong button, enter incorrect content, send the wrong message, delete the wrong data, or perform another unintended action.

2. **Malicious pages or content can try to manipulate the automation process**

   Some web pages, emails, posts, pop-ups, download pages, or other content may deliberately contain misleading instructions designed to make an automated system disclose data, access resources it should not access, perform dangerous operations, or deviate from the user's original task.

3. **Information can leak during attacks, software vulnerabilities, or abnormal conditions**

   Vulnerabilities in the browser, operating system, third-party website, plugin, dependency library, network environment, or Skill itself could theoretically expose local files, browser data, account information, page content, or other data.

4. **Visiting the wrong website or downloading content can introduce security threats**

   Search results, advertisements, redirects, forged pages, malicious downloads, or identification errors can lead the Skill to a dangerous website or cause it to download software or files containing malware, viruses, trojans, or other threats.

5. **Incorrect website actions can disrupt accounts or services**

   On some websites, an incorrect action can cause:

   - content to be published, modified, or deleted incorrectly;
   - email, messages, or forms to be sent incorrectly;
   - an account to be restricted, frozen, or flagged by risk controls;
   - orders, reservations, applications, settings, or other business state to change incorrectly;
   - temporary or long-term loss of normal access to a website or service.

6. **Some actions can have real-world consequences**

   If the Skill is used for payments, transactions, work processes, contracts, account permissions, social relationships, public content, personal identity, important files, or other high-impact scenarios, an incorrect action can cause financial loss, business loss, privacy exposure, reputational harm, or other real-world consequences.

7. **Other risks may exist that these instructions do not anticipate**

   Automation involves browsers, operating systems, third-party websites, network services, and local environments. It is impossible to list every possible risk in advance.

## 3. Recommendations for safer use

To reduce risk, follow these principles:

1. **Do not use it on a device that stores the only copy of important data.**

   If the device contains irreplaceable files, projects, photos, work materials, or other important data, do not use high-privilege automation directly on that device.

2. **Do not use it on a device without backups.**

   Back up important files before use and verify that the backup can be restored.

3. **Use caution in environments containing substantial sensitive information or critical credentials.**

   If the device stores important accounts, passwords, keys, customer data, trade secrets, identity information, payment information, or other sensitive content, use extra caution.

4. **Prefer an isolated environment.**

   Recommended environments include:

   - a sandbox environment;
   - a virtual machine;
   - a test device dedicated to automation;
   - a system account isolated from the primary work environment;
   - a temporary environment that contains no important data.

5. **Require final user confirmation for high-impact tasks.**

   For important actions involving deletion, sending, payment, transactions, publishing, uploading, permission changes, account settings, contracts, applications, and similar operations, the user should personally inspect and confirm the critical step.

6. **Start with low-risk tasks the first time you use the Skill on a website.**

   Begin with opening pages, searching for information, reading content, or organizing text. Confirm that behavior matches expectations before gradually attempting tasks that change website state.

7. **Do not treat the automation system as an infallible executor.**

   Even if the same task has succeeded many times before, a website redesign, network failure, browser upgrade, or other environmental change can produce a different result.

## 4. Risk acceptance

If you choose to use WebMind Windows / Codex on a real device, real account, or real website, make sure you can accept the risks described above as well as other impacts that cannot currently be predicted.

If the device, account, data, or business process cannot tolerate unintended operations, data exposure, account abnormalities, file damage, or other accidents, do not use WebMind Windows / Codex directly in that environment. Prefer a sandbox, virtual machine, test account, or another isolated environment.

**Before using the WebMind Windows / Codex Skill, evaluate whether the risk is acceptable based on the importance of the task, the data stored on the device, and the value of the accounts involved.**

## 5. Permission, isolation, and data boundaries in this edition

These instructions apply only to the **Windows + Codex** `webmind-codex` edition.

**Behavioral rules and code-enforced protections are not the same kind of guarantee.** Requirements such as not capturing login pages, not recording secrets, and operating only within task authorization are primarily behavioral constraints for the model. The project does not contain a security kernel that can reliably recognize every page, identify every secret, and block every dangerous action. The model can still violate those requirements. The initialization gate, Profile metadata checks, last-tab protection, and some parameter validation are code-enforced limits, but they also cannot cover every risk.

CDP should connect only to the local loopback endpoint recorded in the selected Mem. Listening only on loopback does not mean the interface has complete authentication; untrusted local software can still create risk. Do not forward the port, expose the debugging interface, or disable the host sandbox merely to make the project easier to run.

`global.md` must not store credentials, but the browser will store its own session data in the dedicated Profile as part of normal authentication. This does not authorize the Agent to extract, read, or record cookies. **Treat the entire Mem containing the Profile as sensitive data and never upload it publicly.**

Desktop operations in this edition act on the current Windows user session. A private host desktop, focus changes, multiple monitors, and display scaling can all produce results that differ from expectations. Approve only local commands actually needed for the task. Do not disable system protections, change execution policy, or broaden permissions to hide a failure. WSL or a remote terminal is not a substitute for local desktop access.

An isolated environment can support this project only if it actually contains the same target system, visible desktop, browser, and native runtime. A container, remote terminal, or sandbox on another computer does not automatically provide access to your local desktop.

If an error or suspected leak is discovered, stop further changes to external state, avoid propagating any sensitive files that may already have been created, and inform the user promptly. Without user authorization, do not automatically delete evidence, clean files, or attempt remediation.

These instructions are not a certification that the software is "safe," nor a guarantee against consequences affecting accounts, files, business processes, or finances. Use the [User Guide](User%20Guide.md) together with these instructions to decide whether the project is appropriate for your environment.
