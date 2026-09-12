# WebMind macOS / Claude Code Safety Instructions

中文：[安全须知](安全须知.md)

Read these safety instructions carefully before using the WebMind macOS / Claude Code Skill.

WebMind macOS / Claude Code Skill can assist with real actions through a browser, desktop interface, mouse, keyboard, CDP remote debugging, and related mechanisms. These actions may directly affect local files, account state, website data, and real-world business outcomes. Even though the Skill includes multiple safety constraints, it cannot completely eliminate risks from mistakes, malicious pages, software vulnerabilities, or other unforeseen conditions.

## 1. Safety constraints built into the Skill

WebMind macOS / Claude Code Skill includes multiple safety constraints intended to reduce the impact of sensitive-data exposure and incorrect actions, including but not limited to the following:

1. **Do not take screenshots or save sensitive visual content during login or critical data entry**

   Do not take screenshots during sign-in, account recovery, MFA, verification-code entry, CAPTCHA, payment authentication, or similar stages, including when fields are empty or masked. Do not take screenshots while critical private information is visible or being entered. This applies to full-screen, region, browser, CDP, and system screenshots. If an action requires screenshot-based verification during such a stage, pause and hand the step to the user.

2. **Do not write critical private information to Mem**

   WebMind macOS / Claude Code Mem is mainly for reusable operational experience such as website entry points, page structure, stable selectors, and operating procedures.

   Passwords, verification codes, identity information, payment information, access tokens, cookies, private keys, and other sensitive credentials must not be stored in Mem.

3. **Stop automation when a sensitive step must be completed by the user**

   For password entry, verification codes, MFA, CAPTCHA, payment confirmation, and other critical steps that require the user personally, the Skill should stop automatic operation and hand control to the user rather than attempting to bypass the security mechanism.

4. **Stop promptly after recognizing a potentially consequential mistake**

   If the Skill determines that it may have performed an incorrect send, delete, submission, upload, duplicate action, or another action that could have real impact, it should first stop subsequent actions that could continue changing external state and inform the user.

   In this situation, it should not retry, overwrite, undo, delete, or attempt to "fix" the result without user confirmation.

5. **Limit exposure of the browser debugging interface as much as practical**

   When CDP remote debugging is used, WebMind macOS / Claude Code is designed for local-machine use. The remote-debugging port should not be exposed to the public Internet or to an untrusted local network.

6. **Stay within the task scope explicitly authorized by the user**

   The Skill should operate around the goal specified by the user. It must not expand its scope merely because the browser already has saved login state, permissions, or history.

## 2. Safety risks that still remain

The constraints above reduce risk but cannot guarantee absolute safety.

The following situations may still occur in real use:

1. **Incorrect actions may affect data or accounts**

   Because of page-structure changes, element-recognition errors, misunderstanding of context, network delays, website failures, or other causes, the Skill may click the wrong button, enter incorrect content, send the wrong information, delete the wrong data, or perform other unintended actions.

2. **Malicious pages or content may attempt to manipulate the automation process**

   Web pages, email messages, posts, pop-ups, download pages, or other content may intentionally contain misleading instructions designed to induce an automation system to reveal data, access resources it should not access, perform dangerous actions, or deviate from the user's original task.

3. **Attacks, vulnerabilities, or abnormal conditions may cause information exposure**

   If the browser, operating system, third-party website, plugin, dependency, network environment, or the Skill itself contains a vulnerability, local files, browser data, account information, page content, or other data could theoretically be exposed.

4. **Visiting the wrong website or downloading content may introduce security threats**

   Search results, advertisements, redirects, forged pages, malicious downloads, or recognition mistakes may cause the Skill to visit a dangerous website or download files that contain malicious code, viruses, trojans, or other threats.

5. **Incorrect website actions may disrupt an account or service**

   On some websites, an incorrect action may cause:

   - content to be incorrectly published, modified, or deleted;
   - email, messages, or forms to be sent incorrectly;
   - an account to be restricted, frozen, or flagged by risk controls;
   - orders, reservations, applications, settings, or other business states to change incorrectly;
   - temporary or long-term loss of normal access to a website or service.

6. **Some operations may have real-world consequences**

   If the Skill is used for payments, transactions, work activities, contracts, account permissions, social relationships, public content, personal identity, important files, or other high-impact contexts, an incorrect action may cause financial loss, business loss, privacy exposure, reputational harm, or other real-world consequences.

7. **Other risks not anticipated by these instructions may exist**

   Browser automation involves the operating system, third-party websites, network services, the local environment, and multiple other components. It is impossible to list every potential risk in advance.

## 3. Usage recommendations

To reduce risk, follow these principles:

1. **Do not use this system on a device that stores the only copy of important data.**

   If the device contains irreplaceable files, projects, photos, work material, or other important data, do not perform high-privilege automation directly on that device.

2. **Do not use it on a device without backups.**

   Back up important files before use and verify that the backup can actually be restored.

3. **Avoid environments that contain large amounts of important private information or critical credentials.**

   Use extra caution if the device stores important accounts, passwords, keys, customer information, trade secrets, identity information, payment details, or other sensitive content.

4. **Prefer an isolated environment.**

   Recommended environments include:

   - a sandbox environment;
   - a virtual machine;
   - a test device dedicated to automation;
   - a system account isolated from the main work environment;
   - a temporary environment that contains no important data.

5. **Require final user confirmation for high-impact tasks.**

   For deletion, sending, payment, transactions, publication, uploads, permission changes, account settings, contracts, applications, and other important operations, the user should inspect and confirm the critical step personally.

6. **Start with low-risk tasks the first time you use a website.**

   First try opening pages, searching for information, reading content, or organizing text. After confirming that behavior matches expectations, gradually move to tasks that change website state.

7. **Do not treat the automation system as an infallible executor.**

   Even if the same task has succeeded many times before, a website redesign, network failure, browser update, or other changed condition can produce a different result.

## 4. Risk acceptance

If you choose to use WebMind macOS / Claude Code Skill on a real device, real account, or real website, make sure you can accept the risks described above as well as other currently unforeseeable impacts.

If the relevant device, account, data, or business process cannot tolerate an incorrect action, data exposure, account disruption, file damage, or other unexpected result, do not use WebMind macOS / Claude Code Skill directly in that environment. Prefer a sandbox, virtual machine, test account, or another isolated environment.

**Before using WebMind macOS / Claude Code Skill, evaluate the importance of the task, the data stored on the device, and the value of the relevant account, and decide for yourself whether the risk is acceptable.**

## 5. Permissions, isolation, and data boundaries in this distribution

These instructions apply only to the **macOS + Claude Code** `mac-claudecode` distribution.

**Behavioral rules and code-enforced protections are not the same guarantee.** Requirements such as not capturing login pages, not recording secrets, and staying within user authorization are primarily behavioral constraints for the model. The project does not contain a security kernel capable of reliably recognizing every page, identifying every secret, and blocking every dangerous action. The model may still violate these requirements. Initialization gates, Profile metadata verification, final-tab protection, and some argument validation are implemented in code, but they also cannot cover every risk.

CDP should connect only to the local loopback endpoint recorded in the selected Mem. Even when the endpoint listens only on loopback, that does not mean it has complete authentication. Untrusted software on the same machine can still present risk. Do not forward the port, expose the debugging interface, or disable the host sandbox for convenience.

`global.md` must not contain credentials, but the browser may store its own session data in the dedicated Profile as part of normal sign-in behavior. This does not authorize the Agent to extract, read, or record cookies. **Treat the entire Mem that contains a Profile as sensitive data and do not upload it publicly.**

Screen Recording and Accessibility permissions may give the actual host process broad observation or input capabilities. Grant them only to a trusted host and only for controlled use cases. The LaunchServices helper is for browser process management and is not a permission-bypass mechanism. Do not disable macOS privacy protections or the host sandbox. When a required permission is missing, the user should decide through the normal system mechanism whether to grant it.

An isolated environment can support this project only if it actually contains the same target system, visible desktop, browser, and native runtime environment. A container, remote terminal, or sandbox on another computer does not automatically provide access to your local Mac desktop.

If an error or suspected leak is discovered, stop further external state changes, avoid propagating any sensitive files that may already have been created, and inform the user promptly. Do not automatically delete evidence, clean files, or attempt remediation without user authorization.

These instructions are not a certification that the software is "safe" and do not guarantee outcomes for accounts, files, business operations, or financial consequences. Use the [User Guide](User%20Guide.md) together with these instructions to decide whether this project is appropriate for your environment.
