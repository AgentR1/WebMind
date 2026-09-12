# WebMind macOS / Codex Safety Instructions

Read these Safety Instructions carefully before using the WebMind macOS / Codex Skill.

The WebMind macOS / Codex Skill can assist with real operations through a browser, desktop UI, mouse, keyboard, and CDP remote debugging. Because these operations can directly affect local files, account state, website data, and real-world business outcomes, the included safety restrictions cannot completely eliminate the risk of mistakes, malicious pages, software vulnerabilities, or other unforeseen events.

Chinese version: [安全说明](%E5%AE%89%E5%85%A8%E8%AF%B4%E6%98%8E.md).

## 1. Safety restrictions already included in the Skill

The WebMind macOS / Codex Skill includes multiple safety constraints intended to reduce the impact of sensitive-information exposure and incorrect actions, including but not limited to the following.

1. **Do not capture or save sensitive screens during authentication or critical-data entry**

   Do not take screenshots during sign-in, account recovery, MFA, verification-code entry, CAPTCHA, payment authentication, or similar stages, even when fields are empty or masked. Do not take screenshots while critical private data is visible or being entered. This applies to full-screen, regional, browser, CDP, and system screenshots. If an operation depends on a screenshot during such a stage, pause and let the user complete the step.

2. **Do not write critical private information to Mem**

   WebMind macOS / Codex Mem is intended for reusable operational knowledge such as website entry points, page structure, stable selectors, and verified procedures.

   Passwords, verification codes, identity information, payment information, access tokens, cookies, private keys, and other sensitive credentials must not be saved to Mem.

3. **Stop automated operation when a sensitive step must be completed by the user**

   For password entry, verification codes, MFA, CAPTCHA, payment confirmation, and other critical steps that require the user, the Skill should stop automated operation and hand control to the user instead of attempting to bypass the security mechanism.

4. **Stop promptly when a real-impact mistake may already have happened**

   If the Skill determines that it may have performed an incorrect send, deletion, submission, upload, duplicate action, or another operation with real external impact, it should prioritize stopping any further state-changing activity and inform the user.

   In that situation, it must not continue retrying, overwriting, undoing, deleting, or otherwise attempting to "fix" the result without user confirmation.

5. **Limit exposure of the browser debugging interface**

   When using CDP remote debugging, WebMind macOS / Codex is intended to use a local interface. Do not expose the remote-debugging port to the public internet or an untrusted local network.

6. **Stay within the task scope explicitly authorized by the user**

   The Skill should operate only toward the user's stated goal. Existing browser sessions, permissions, or historical data do not authorize it to expand the scope of the task.

## 2. Risks that still remain

The restrictions above can reduce risk but cannot guarantee absolute safety.

The following situations can still occur in real use.

1. **Incorrect actions can affect data or accounts**

   Page changes, element-recognition errors, context misunderstandings, network delay, website faults, or other causes can make the Skill click the wrong control, enter incorrect content, send the wrong information, delete the wrong data, or perform another unintended action.

2. **Malicious pages or malicious content can try to manipulate automation**

   Webpages, emails, posts, popups, download pages, and other content can intentionally contain misleading instructions intended to make an automated system disclose data, access unauthorized resources, execute dangerous actions, or deviate from the user's actual task.

3. **Attacks, software vulnerabilities, or abnormal conditions can expose information**

   Vulnerabilities in the browser, operating system, third-party website, plugin, dependency library, network environment, or the Skill itself could theoretically expose local files, browser data, account information, page content, or other information.

4. **Visiting the wrong site or downloading the wrong content can introduce security threats**

   Search results, advertising, redirects, forged pages, malicious downloads, or recognition mistakes can lead the Skill to a dangerous website or cause it to download malware, viruses, trojans, or other harmful files.

5. **Incorrect website operations can disrupt accounts or services**

   On some websites, an incorrect action can result in:

   - content being incorrectly published, changed, or deleted;
   - emails, messages, or forms being sent incorrectly;
   - an account being limited, frozen, or flagged by risk controls;
   - orders, appointments, applications, settings, or other business state changing incorrectly;
   - temporary or long-term loss of normal access to a website or service.

6. **Some operations can have real-world consequences**

   If the Skill is used for payments, transactions, business work, contracts, account permissions, social relationships, public content, personal identity, important files, or other high-impact scenarios, a mistake can lead to financial loss, business loss, privacy exposure, reputational impact, or other real-world consequences.

7. **Other risks may exist that these instructions do not anticipate**

   Automation spans browsers, operating systems, third-party websites, network services, and local environments. It is not possible to enumerate every risk in advance.

## 3. Usage recommendations

To reduce risk, follow these principles.

1. **Do not use the Skill on a device that stores the only copy of important data.**

   If a device contains irreplaceable files, projects, photos, work material, or other important data, avoid using high-permission automation directly on that device.

2. **Do not use it on a device without backups.**

   Back up important files before use and make sure the backup can actually be restored.

3. **Avoid environments that contain large amounts of important private data or critical credentials.**

   Use caution if the device stores important accounts, passwords, keys, customer information, trade secrets, identity information, payment data, or other sensitive content.

4. **Prefer an isolated environment.**

   Recommended environments include:

   - a sandbox;
   - a virtual machine;
   - a test device dedicated to automation;
   - a system account isolated from the primary work environment;
   - a temporary environment that does not contain important data.

5. **Require user confirmation for high-impact tasks.**

   For deletion, sending, payment, transactions, publishing, uploading, permission changes, account settings, contracts, applications, and similar important actions, have the user inspect and confirm the critical step.

6. **Start with low-risk tasks on a website you have not used before.**

   Begin with actions such as opening pages, searching for information, reading content, or organizing text. Confirm that behavior is as expected before gradually attempting actions that change website state.

7. **Do not treat an automation system as an infallible executor.**

   A task that succeeded many times before can still behave differently after a website redesign, network problem, browser update, or other environmental change.

## 4. Risk acceptance

If you choose to use the WebMind macOS / Codex Skill with a real device, real account, or real website, make sure you can accept the risks described above as well as other effects that cannot currently be predicted.

If the device, account, data, or business process cannot tolerate mistakes, data exposure, account disruption, file damage, or other unexpected events, do not use WebMind macOS / Codex directly in that environment. Prefer a sandbox, virtual machine, test account, or another isolated environment.

**Before using the WebMind macOS / Codex Skill, judge whether the risk is acceptable based on the importance of the task, the value of data stored on the device, and the value of the account involved.**

## 5. Permissions, isolation, and data boundaries in this distribution

These instructions apply only to the **macOS + Codex** `mac-codex` distribution.

**Behavioral rules and code-enforced protections are not the same guarantee.** Requirements such as not capturing authentication screens, not recording secrets, and staying within task authorization are primarily behavioral constraints for the model. The project does not contain a security kernel that can reliably identify every sensitive page, identify every secret, and block every dangerous action. The model can still violate those requirements. Initialization gates, Profile metadata verification, final-tab protection, and some parameter validation are program-enforced restrictions, but they also cannot cover every risk.

CDP should connect only to the local loopback interface recorded in the selected Mem. Even a loopback-only interface does not imply complete authentication; untrusted software on the same computer may still create risk. Do not forward the port, expose the debugging interface, or disable host sandboxing merely to make operation easier.

`global.md` must not contain credentials, but the dedicated browser Profile can store its own session data so normal sign-in can persist. That does not authorize the Agent to extract, read, or record cookies. **Treat the entire Mem that contains the Profile as sensitive data and never upload it publicly.**

Screen Recording and Accessibility permissions can grant the actual host process broad observation or input capability. Grant them only to a trusted host and control the situations in which they are used. The LaunchServices helper is for browser-process management, not for bypassing permissions. Do not disable system privacy protections or the host sandbox. When permission is missing, let the user decide through the normal operating-system mechanism whether to grant it.

An isolated environment can support this project only if it actually contains the same target system, visible desktop, browser, and native runtime environment. A container, remote terminal, or sandbox on another computer does not automatically provide visibility into the user's local desktop.

If an error or suspected leak occurs, stop further external state changes, avoid spreading any sensitive artifact that has already been produced, and inform the user promptly. Do not automatically delete evidence, clean up files, or attempt remediation without user authorization.

These instructions are not a certification that the software is "safe" and do not guarantee protection from account, file, business, or financial consequences. Use the [User Guide](User%20Guide.md) to judge whether this project is appropriate for your environment. Report security issues privately according to [SECURITY.md](SECURITY.md); do not disclose vulnerabilities, account information, or sensitive logs in a public Issue.
