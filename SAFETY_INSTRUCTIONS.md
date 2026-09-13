# WebMind Windows / Claude Code Safety Instructions

Chinese version: [安全须知](安全须知.md)

Read these Safety Instructions carefully before using the WebMind Windows / Claude Code Skill.

WebMind Windows / Claude Code Skill can perform real operations through a browser, desktop UI, mouse, keyboard, and CDP remote debugging. Because these actions can directly affect local files, account state, website data, and real-world business outcomes, the safety restrictions built into the Skill cannot completely eliminate risks caused by mistakes, malicious pages, software vulnerabilities, or other unforeseen factors.

## 1. Safety restrictions already built into the Skill

WebMind Windows / Claude Code Skill includes multiple safety constraints intended to reduce the impact of sensitive-data exposure and incorrect actions, including but not limited to the following:

1. **Do not capture or save sensitive screens during login and critical-data entry**

   During login, account recovery, MFA, verification-code, CAPTCHA, payment-authentication, and similar phases, screenshots must not be taken, even when fields are empty or masked. Screenshots are also prohibited while critical private data is visible or being entered. This rule applies to full-screen, regional, browser, CDP, and system screenshots. Operations that require screenshot confirmation must pause and be handed to the user during those phases.

2. **Do not write critical private information into Mem**

   WebMind Windows / Claude Code Mem is intended for reusable operational knowledge such as site entry points, page structure, stable selectors, and workflow steps.

   Passwords, verification codes, identity data, payment information, access tokens, cookies, private keys, and other sensitive credentials must not be saved in Mem.

3. **Stop automation for sensitive steps that must be completed by the user**

   For password entry, verification codes, MFA, CAPTCHA, payment confirmation, and other critical steps that require the user personally, the Skill should stop automation and hand control to the user rather than trying to bypass the security mechanism.

4. **Stop promptly when a consequential mistake is known or suspected**

   If the Skill believes it may have sent the wrong content, deleted the wrong item, submitted to the wrong target, uploaded the wrong file, duplicated an action, or otherwise caused a real-world unintended effect, it should prioritize stopping further state-changing operations and inform the user.

   In that situation, it should not retry, overwrite, undo, delete, or attempt to "fix" the result without the user's confirmation.

5. **Limit exposure of the browser debugging interface**

   When using CDP remote debugging, WebMind Windows / Claude Code is designed for local-machine use. Do not expose the remote-debugging port to the public Internet or an untrusted local network.

6. **Operate within the user's explicit task scope**

   The Skill should work toward the target specified by the user. Existing browser login state, permissions, or history do not authorize the Skill to expand the operation beyond that scope.

## 2. Security risks that still remain

The restrictions above reduce risk but cannot guarantee absolute safety.

The following situations may still occur in real use:

1. **Incorrect operations can affect data or accounts**

   Page-layout changes, element-recognition errors, context misunderstandings, network delays, website failures, or other conditions may cause the Skill to click the wrong button, enter incorrect content, send the wrong message, delete the wrong data, or perform another unintended action.

2. **Malicious pages or content can try to manipulate automation**

   Web pages, emails, posts, pop-ups, download pages, or other content may deliberately include misleading instructions intended to make an automated system disclose data, access unauthorized resources, perform dangerous actions, or deviate from the user's original task.

3. **Attacks, software vulnerabilities, or abnormal conditions can expose information**

   Vulnerabilities in the browser, operating system, third-party websites, plugins, dependencies, network environment, or the Skill itself could theoretically expose local files, browser data, account information, page content, or other data.

4. **Incorrect site visits or downloads can introduce security threats**

   Search results, advertisements, redirects, spoofed pages, malicious downloads, or recognition errors may lead the Skill to dangerous websites or cause it to download files or software containing malicious code, viruses, trojans, or other threats.

5. **Incorrect website actions can disrupt accounts or services**

   On some websites, mistakes can cause:

   - content to be published, modified, or deleted incorrectly;
   - emails, messages, or forms to be sent incorrectly;
   - accounts to be restricted, frozen, or flagged by risk controls;
   - orders, reservations, applications, settings, or other business state to change incorrectly;
   - short-term or long-term loss of normal access to a website or service.

6. **Some operations can have real-world consequences**

   If the Skill is used for payments, transactions, work processes, contracts, account permissions, social relationships, public content, personal identity, important files, or other high-impact scenarios, mistakes can lead to financial loss, business loss, privacy exposure, reputational harm, or other real-world consequences.

7. **Other risks may exist that are not covered here**

   Browser automation spans the browser, operating system, third-party websites, network services, and local environment, so it is impossible to enumerate every possible risk in advance.

## 3. Recommended precautions

To reduce risk, follow these principles:

1. **Do not use it on a device that stores the only copy of important data.**

   If a device contains irreplaceable files, projects, photos, work materials, or other important data, do not perform high-privilege automation directly on that device.

2. **Do not use it on a device without backups.**

   Back up important files before use and make sure the backup can actually be restored.

3. **Avoid environments that contain large amounts of sensitive data or critical credentials.**

   Use extra caution if the device stores important accounts, passwords, keys, customer data, trade secrets, identity information, payment information, or other sensitive content.

4. **Prefer an isolated environment.**

   Recommended environments include:

   - a sandbox;
   - a virtual machine;
   - a dedicated test device for automation;
   - a system account isolated from the main work environment;
   - a temporary environment with no important data.

5. **Require final user confirmation for high-impact tasks.**

   For deletion, sending, payments, transactions, publishing, uploading, permission changes, account settings, contracts, applications, and similar important actions, the user should inspect and confirm critical steps personally.

6. **Start with low-risk tasks on a new website.**

   Begin with opening pages, searching information, reading content, or organizing text. After confirming that the workflow behaves as expected, gradually move to tasks that change website state.

7. **Do not treat automation as an infallible executor.**

   Even if a task has succeeded many times before, a website redesign, network failure, browser upgrade, or other environmental change can produce a different result.

## 4. Risk acceptance

If you choose to use WebMind Windows / Claude Code Skill on real devices, real accounts, or real websites, make sure you can accept the risks described above as well as other consequences that cannot currently be predicted.

If the device, account, data, or business process cannot tolerate incorrect operations, data exposure, account problems, file damage, or other accidents, do not use WebMind Windows / Claude Code Skill directly in that environment. Prefer a sandbox, virtual machine, test account, or other isolated environment.

**Before using WebMind Windows / Claude Code Skill, evaluate whether the risk is acceptable based on the importance of the task, the data stored on the device, and the value of the account involved.**

## 5. Permission, isolation, and data boundaries in this distribution

These instructions apply only to the **Windows + Claude Code** `windows-claudecode` distribution.

**Behavioral rules and code-enforced protections are not the same guarantee.** Requirements such as not capturing login pages, not recording secrets, and staying within the task authorization are primarily behavioral constraints for the model; the project does not contain a security kernel that can reliably identify every page, detect every secret, and block every dangerous action. The model can still violate those requirements. Initialization gates, Profile metadata checks, last-tab protection, and some parameter validation are code-enforced restrictions, but they also do not cover every risk.

CDP should connect only to the local loopback endpoint recorded in the selected Mem. Restricting the interface to loopback does not mean it has complete authentication; untrusted programs on the same machine can still pose a risk. Do not forward the port, expose the debugging interface, or disable the host sandbox for convenience.

`global.md` must not contain credentials, but the browser may retain its own session data inside the dedicated Profile as part of normal sign-in behavior. This does not authorize the Agent to extract, read, or record cookies. **Treat the entire Mem containing the Profile as sensitive data and do not upload it publicly.**

Desktop operations in this edition affect the current Windows user session. Host-private desktops, focus changes, multiple monitors, and display scaling can produce results different from what was expected. Approve only local commands that are actually necessary; do not disable system protections, alter execution policy, or broaden permissions merely to conceal a failure.

An isolated environment can support this project only if it actually contains the same target system, visible desktop, browser, and native runtime environment. A container, remote terminal, or sandbox on another computer does not automatically provide access to your local desktop.

If an error or suspected leak is discovered, stop further external state changes, avoid propagating any sensitive files that may have been produced, and inform the user promptly. Do not automatically delete evidence, clean up files, or attempt remediation without the user's authorization.

These instructions are not a certification that the software is "safe," nor are they a guarantee against consequences affecting accounts, files, business operations, or finances. Use the [User Guide](USER_GUIDE.md) together with these instructions to decide whether WebMind is appropriate for your environment.
