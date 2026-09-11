# WebUse for Codex 使用教程

## 一、项目简介

WebUse for Codex 是一个面向 **本机 Codex 环境** 的网页与桌面自动化 Skill，作用是让 Codex 在获得你的授权后，能够通过本机 shell、浏览器和桌面交互能力完成网页浏览、点击、输入、页面读取、截图识别以及重复性的网页操作。

项目可以为 Codex 提供如下能力：

- **CDP 浏览器控制**：通过 Chrome DevTools Protocol 读取网页结构、定位元素、点击、输入、导航、执行 JavaScript、截图等。
- **桌面截图**：截取整个屏幕或指定区域，用于视觉识别和操作后的状态确认。
- **鼠标控制**：移动、点击、按住和滚动等桌面操作。
- **键盘输入**：输入 ASCII 文本、按键和常用组合快捷键；网页中的中文等 Unicode 文本优先通过 CDP 输入。
- **等待与状态检查**：执行一次两秒等待，然后重新检查页面或桌面状态。
- **Mem 外部记忆**：任务开始前读取与网站相关的已有经验，成功结束后整理并保存真正可复用的操作经验。

WebUse 有两种主要使用方式：

1. 直接操作你平常正在使用的 Chrome，以截图、鼠标和键盘为主。
2. 使用 WebUse 独立的 Chrome 调试 Profile，通过 CDP 执行网页操作。

第二种方式通常速度更快、Token 消耗更低、网页定位更稳定；第一种方式则更容易直接继承你日常 Chrome 已有的登录状态。

---

## 二、安装方式

### 2.1 最简单的安装方式

首先将压缩包解压到一个固定位置，然后找到 `webuse-codex` 文件夹的**完整路径**。

例如 Windows 中可能是：

```text
D:\Tools\webuse-codex
```

macOS 中可能是：

```text
/Users/你的用户名/Tools/webuse-codex
```

复制这个路径，然后打开**本机 Codex**，直接告诉 Codex：

```text
请从这个本地路径中直接安装 WebUse Codex Skill，并完成所需依赖安装和环境检查：
D:\Tools\webuse-codex
```

macOS 示例：

```text
请从这个本地路径中直接安装 WebUse Codex Skill，并完成所需依赖安装和环境检查：
/Users/你的用户名/Tools/webuse-codex
```

如果 Codex 可以访问这个本地目录并执行 shell 命令，它可以读取项目中的 `SKILL.md`、安装脚本和说明文件，再按照项目提供的安装方式完成配置。

> WebUse for Codex 是本机 Skill。它要求 Codex 能在你的 Windows 或 macOS 本机执行命令，并不是让云端 Codex 远程控制你的电脑。

### 2.2 其它安装方式：使用项目安装脚本

Codex 版提供了完整安装器。默认情况下，Skill 会安装到：

```text
~/.agents/skills/webuse-codex
```

运行数据则保存在独立目录中。

默认运行数据位置：

- Windows：`%LOCALAPPDATA%\WebUseCodex`
- macOS：`~/Library/Application Support/WebUseCodex`

#### Windows

使用**原生 PowerShell**进入 `webuse-codex` 源目录，然后运行：

```powershell
& '.\scripts\install.ps1'
```

安装后检查：

```powershell
& "$HOME\.agents\skills\webuse-codex\scripts\webuse.ps1" doctor --json
```

如果 PowerShell 执行策略阻止本地 `.ps1`，不需要修改系统安全策略，可以使用 Python 入口：

```powershell
py -3 -B '.\scripts\install.py'
py -3 -B "$HOME\.agents\skills\webuse-codex\scripts\bootstrap.py" doctor --json
```

#### macOS

进入 `webuse-codex` 源目录，然后运行：

```bash
bash './scripts/install.sh'
```

安装后检查：

```bash
bash "$HOME/.agents/skills/webuse-codex/scripts/webuse.sh" doctor --json
```

### 2.3 项目级安装

如果只希望某一个 Codex 项目使用 WebUse，可以采用项目级安装。

Windows：

```powershell
& '.\scripts\install.ps1' --scope project --project 'D:\Projects\My project'
```

macOS：

```bash
bash './scripts/install.sh' --scope project --project "$HOME/Projects/My project"
```

### 2.4 自定义运行数据目录

Windows 示例：

```powershell
& '.\scripts\install.ps1' --data-dir 'D:\WebUseCodex Data'
```

macOS 示例：

```bash
bash './scripts/install.sh' --data-dir "$HOME/WebUseCodex Data"
```

安装器会记录自定义数据路径，后续升级仍会继续使用。

也可以使用：

```text
WEBUSE_CODEX_DATA_DIR
```

指定运行数据位置。

### 2.5 可选 AGENTS 路由规则

如果希望 Codex 更容易自动判断何时使用 WebUse，可以在安装时显式加入：

```text
--add-agent-rules
```

例如 Windows：

```powershell
& '.\scripts\install.ps1' --add-agent-rules
```

macOS：

```bash
bash './scripts/install.sh' --add-agent-rules
```

这是**可选项**。默认安装不会修改你的全局 `AGENTS.md` 或 Codex 配置。

### 2.6 安装后让 Codex 识别 Skill

安装完成后建议重新打开一个本机 Codex 会话。

可以使用：

```text
/skills
```

检查是否已经出现 `webuse-codex`。

也可以直接显式调用：

```text
$webuse-codex 请使用 WebUse 完成这个网页任务。
```

---

## 三、安装后的检查与环境准备

### 3.0 最简单的检查方式

如果你不想阅读3.1-3.6中有关环境配置检查的要求
你也可以采用最简单的方式检查环境：
（在Codex中：
```text
请帮我检查webuse系列skill的运行环境是否正常；然后尝试启用其中的CDP打开浏览器，看看能否正常使用。
```

### 3.1 基础环境要求

建议准备：

- **本机 Codex**，并且可以执行本机 shell 命令；
- **Python 3.10 或更高版本**；
- **Google Chrome**，也可以使用项目能够识别的 Chromium / Edge；
- Windows 使用原生 Windows Python / PowerShell，不要使用 WSL 中的 Linux Python 操作 Windows 桌面；
- macOS 需要给实际执行 Codex/Python 的宿主应用授予“屏幕录制”和“辅助功能”权限。

项目本身不需要单独配置 OpenAI API Key，它使用的是你现有的本机 Codex 会话。

### 3.2 检查 Python

Windows：

```powershell
py -3 --version
```

或：

```powershell
python --version
```

macOS：

```bash
python3 --version
```

建议至少 Python 3.10；如果自行选择环境，Python 3.11 / 3.12 通常是比较稳妥的版本。

### 3.3 执行 doctor 检查

Windows：

```powershell
& "$HOME\.agents\skills\webuse-codex\scripts\webuse.ps1" doctor --json
```

macOS：

```bash
bash "$HOME/.agents/skills/webuse-codex/scripts/webuse.sh" doctor --json
```

重点确认：

- Skill 安装路径正常；
- Runtime 数据目录可写；
- Python 虚拟环境和依赖正常；
- Chrome / Chromium / Edge 能被找到；
- 当前宿主能够访问用户桌面；
- macOS 屏幕录制、辅助功能权限是否正常。

### 3.4 Windows 特别检查

不要让 Codex 使用 WSL 中的 Linux Python 去控制 Windows 桌面。

另外，部分 Codex Windows 沙箱环境可能运行在一个与用户当前桌面隔离的私有 Desktop 中。此时截图、鼠标和日常 Chrome 窗口彼此不可见。

WebUse 会尝试识别已知的非交互桌面。如果诊断提示当前命令无法访问用户桌面，需要通过 Codex 对具体本机命令的授权机制执行，或者在已登录用户自己的 PowerShell 中运行对应命令。

WebUse 不会自动关闭 Codex 沙箱，也不会主动修改系统 ACL、防火墙或全局安全设置。

### 3.5 macOS 特别检查

进入：

```text
系统设置 > 隐私与安全性
```

给实际执行 WebUse 的应用授予：

- **屏幕录制**
- **辅助功能**

这里的“应用”可能是 Terminal、iTerm、IDE 或 Codex 桌面宿主，具体取决于你实际从哪里运行 Codex。

权限修改后请完全退出并重新打开对应应用。

### 3.6 CDP 使用前需要准备 Chrome

WebUse **不会附带 Chrome 浏览器可执行文件**。

使用 CDP 前，请先在本机安装：

- Google Chrome；或
- 项目能够识别的 Chromium / Microsoft Edge。

Codex 版默认 CDP 地址为：

```text
http://127.0.0.1:9223
```

默认专用浏览器 Profile 位于：

```text
<WebUseCodex数据目录>/chrome-profile
```

它与 Claude Code 版默认使用的 9222 端口和 `WebUse` 数据目录相互隔离，因此两个版本可以在同一台电脑中并存且互不影响。

### 3.7 启动 CDP 专用浏览器

Windows：

```powershell
& "$HOME\.agents\skills\webuse-codex\scripts\webuse.ps1" cdp launch --json
```

macOS：

```bash
bash "$HOME/.agents/skills/webuse-codex/scripts/webuse.sh" cdp launch --json
```

第一次启动时会打开一套独立于日常 Chrome 默认 Profile 的浏览器环境。

需要登录的网站请在该窗口中手动完成第一次登录。

### 3.8 检查 CDP 是否正常

Windows：

```powershell
& "$HOME\.agents\skills\webuse-codex\scripts\webuse.ps1" cdp self-check --json
```

macOS：

```bash
bash "$HOME/.agents/skills/webuse-codex/scripts/webuse.sh" cdp self-check --json
```

进一步查看浏览器标签页：

Windows：

```powershell
& "$HOME\.agents\skills\webuse-codex\scripts\webuse.ps1" cdp tabs --json
```

macOS：

```bash
bash "$HOME/.agents/skills/webuse-codex/scripts/webuse.sh" cdp tabs --json
```

如果 `self-check` 能正常返回，并且 `tabs` 能看到当前调试浏览器的页面，说明 CDP 基本正常。

---

## 四、重要提示

### 1.目前，该项目支持两种使用模式：

#### 使用模式一：直接使用你平常使用的 Chrome

第一种方式是直接使用你的**原始 Chrome，也就是你平常正在使用的那个 Chrome**。

由于 Chrome 官方的安全限制，WebUse 不应直接把日常默认浏览器 Profile 当成自己的远程调试 Profile，因此这种方式通常**无法使用 CDP 功能**。

尽管如此，此 Skill 仍然支持最基础且非常实用的桌面视觉识别、截图、鼠标点击和键盘输入，因此大部分普通网页任务仍旧能够完成。

但是在这种模式下，由于 Codex 不能直接通过 CDP 获取网页 DOM、选择器和内部状态，通常需要更多截图和视觉确认，所以：

- 花费时间会显著增加；
- Token 消耗会明显增加；
- 页面定位和复杂交互的稳定性通常低于 CDP 模式。

它的优势同样很明显：使用的是你每天使用的那个 Chrome，所以日常网站的 Cookie、登录态和现有会话通常可以直接保留。

因此在很多情况下，你不需要重新登录，也不需要额外进行任何手动操作。

#### 使用模式二： 使用 Chrome 远程调试浏览器

第二种方式是使用 **Chrome 远程调试浏览器**，可以理解为 WebUse / Codex 专用的一套浏览器 Profile。

它并不是 Skill 内置了一份新的 Chrome 浏览器程序，而是使用电脑上已经安装的 Chrome / Chromium / Edge，同时创建一套独立且持久化的 `chrome-profile`。

在这个方式下可以使用 CDP 功能，Codex 能够直接获取网页结构、定位元素、点击、输入和检查执行结果，任务通常更加便捷、快速，同时能减少截图和 Token 消耗。

只要你不主动删除 WebUseCodex 数据目录、删除 `chrome-profile`，或者被杀毒软件、系统清理工具、磁盘清理工具等误删，这套专用浏览器 Profile 通常不会自动重置。

因此可以把它理解为一套长期保存的“Codex / WebUse 专用 Chrome Profile”：

- 所有需要账号的网站，第一次使用时通常需要你手动登录；
- 完成登录后，Session/Cookie 会被保存在该专用 Profile 中；
- 只要该 Profile 没有被清理，第二次访问相同网站时通常无需再次登录。

请不要将这个包含登录状态的 `chrome-profile` 打包发布或分享给其他人，也不要直接复制一个正在运行中的日常 Chrome Profile 给调试浏览器使用。

Codex 环境中如果同时安装了其它浏览器控制 Skill、插件或自动化工具，模型有时可能会选择其它方案。若你希望固定由 WebUse 执行，建议在提示词中明确要求：

```text
只使用 WebUse 完成本任务，不要切换到其它浏览器控制插件或 Skill。
```

### 2. 登录、验证码和敏感操作

遇到以下内容时，建议由你本人完成：

- 用户名、密码等敏感凭证；
- MFA / 两步验证；
- CAPTCHA / 人机验证；
- 支付认证；
- 其它高敏感身份确认操作。

完成后告诉 Codex 继续即可。

### 3. 不要随意清理 WebUseCodex 数据目录

默认运行数据位置：

- Windows：`%LOCALAPPDATA%\WebUseCodex`
- macOS：`~/Library/Application Support/WebUseCodex`

这里通常保存：

- 独立 Python 环境；
- CDP 专用 `chrome-profile`；
- Mem 外部记忆。

如果将整个目录删除，专用浏览器登录态与 Mem 也可能一并消失。

---

## 五、推荐使用方式

### 如果希望使用模式一 ：直接操作日常 Chrome

建议在任务开始时使用：

```text
请使用 $webuse-codex / WebUse Skill 完成任务，不要使用CDP或远程调试功能，直接使用我正在使用的chrome浏览器，不要切换到其它浏览器控制插件或Skill。开始前读取相关 Mem 记忆，结束后记录可复用经验。任务是...
```

适合：

- 网站已经在你的日常 Chrome 中登录；
- 不希望为专用浏览器重新登录；
- 任务步骤较少；
- 可以接受执行速度较慢和更多 Token 消耗。

### 如果希望使用模式二 ：使用 CDP 专用浏览器

建议使用：

```text
请使用 $webuse-codex / WebUse Skill 完成任务，使用CDP远程调试功能并在调试版chrome中操作，不要切换到其它浏览器控制插件或Skill。开始前读取相关 Mem 记忆，结束后记录可复用经验。任务是...
```

适合：

- 经常需要 Codex 操作网页；
- 希望执行更快、更稳定；
- 网页任务步骤复杂；
- 希望减少截图识别次数和 Token 消耗；
- 可以接受在第一次访问网站时在专用浏览器中手动完成一次登录。

对于长期、频繁使用，通常更推荐 **方式 2：CDP 专用浏览器**。常用网站第一次登录完成后，它能够同时兼顾执行效率、稳定性和长期登录状态。


---

## 六、使用建议

### 可以用以下任务快速体验 WebUse

第一次体验时，建议优先使用 **CDP 专用浏览器模式**。如果网站尚未登录，请在 WebUse 打开的调试版 Chrome 中手动完成一次登录，然后再让 Codex 继续。

#### 示例 1：Gmail 邮件撰写与发送

将收件人替换为你自己的测试邮箱：

```text
请使用 $webuse-codex / WebUse Skill 完成任务，使用CDP远程调试功能并在调试版chrome中操作，不要切换到其它浏览器控制插件或Skill。开始前读取相关 Mem 记忆，结束后记录可复用经验。

任务：在 Chrome 中打开 Gmail，给 ???@???.com 发送一封邮件。主题为 Sorry，正文请帮我撰写，约 200 字，大意是：很抱歉我错过了晚餐，因为会议延迟了；我想明天邀请对方一起吃晚餐。
```

#### 示例 2：Gmail 邀请邮件

```text
请使用 $webuse-codex / WebUse Skill 完成任务，使用CDP远程调试功能并在调试版chrome中操作，不要切换到其它浏览器控制插件或Skill。开始前读取相关 Mem 记忆，结束后记录可复用经验。

任务：在 Chrome 中打开 Gmail，给 ???@???.com 发送一封邮件。主题为 Hello，正文请帮我撰写，约 200 字，大意是：昨天见到你很高兴，想邀请你今天晚上 22:00 一起吃宵夜。
```

> 邮件发送属于对外产生实际影响的操作。第一次测试时，建议使用你自己的备用邮箱作为收件人，并在发送前检查收件人、主题和正文。

#### 示例 3：知乎检索、总结并保存到桌面

```text
请使用 $webuse-codex / WebUse Skill 完成任务，使用CDP远程调试功能并在调试版chrome中操作，不要切换到其它浏览器控制插件或Skill。开始前读取相关 Mem 记忆，结束后记录可复用经验。

任务：在 Chrome 中打开知乎，搜索“Claude Code 使用技巧”相关帖子，选择一个赞同数高于 100 的帖子，阅读并总结主要内容为一段文字，然后保存到桌面文件 Answer.txt。
```

#### 示例 4：知乎指定主题检索与文件保存

```text
请使用 $webuse-codex / WebUse Skill 完成任务，使用CDP远程调试功能并在调试版chrome中操作，不要切换到其它浏览器控制插件或Skill。开始前读取相关 Mem 记忆，结束后记录可复用经验。

任务：在 Chrome 中打开知乎，搜索“Codex 的前世今生”相关帖子，打开搜索结果中的第一个相关帖子，阅读并总结主要内容为一段文字，然后保存到桌面文件 Answer.txt。
```

这些示例分别覆盖了网页打开、登录态复用、CDP 页面控制、表单填写、网页搜索、内容读取、Mem 记忆以及本地文件写入等能力，适合作为安装完成后的基础体验任务。
