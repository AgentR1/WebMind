# WebUse for Claude Code 使用教程

## 一、项目简介

WebUse for Claude Code 是一个面向 **Claude Code 本机环境** 的网页与桌面自动化插件，作用是让 Claude Code 在获得你的授权后，能够直接操作本机浏览器和部分桌面界面，完成网页浏览、点击、输入、读取页面、截图识别以及重复性的网页操作。

项目可以为 Claude Code 提供如下能力：

- **CDP 浏览器控制**：通过 Chrome DevTools Protocol 读取网页结构、定位元素、点击、输入、跳转页面、执行 JavaScript、截图等。
- **桌面截图**：截取整个屏幕或指定区域，用于视觉识别和状态确认。
- **鼠标控制**：移动、点击、按住、滚动等基础桌面操作。
- **键盘输入**：输入文字、按键和组合快捷键。
- **等待与状态检查**：在网页加载、弹窗出现、任务处理等场景中按固定节奏等待并重新确认页面状态。
- **Mem 外部记忆**：在任务开始前读取与网站相关的操作经验，在任务结束后整理并保存可复用经验，减少下一次执行同类任务时的摸索成本。

WebUse 有两种主要使用方式：

1. 直接操作你平常正在使用的 Chrome，以截图、鼠标和键盘为主。
2. 使用 WebUse 独立的 Chrome 调试 Profile，通过 CDP 执行网页操作。

第二种方式通常速度更快、Token 消耗更低、网页定位更稳定；第一种方式则更容易直接继承你日常浏览器已有的登录状态。

---

## 二、安装方式

### 2.1 最简单的安装方式

首先将压缩包解压到一个固定位置，然后找到 `webuse-claudecode` 文件夹的**完整路径**。

例如 Windows 中可能是：

```text
D:\Tools\webuse-claudecode
```

macOS 中可能是：

```text
/Users/你的用户名/Tools/webuse-claudecode
```

复制这个路径，然后打开 Claude Code，直接告诉 Claude Code：

```text
请从这个本地路径中直接安装 WebUse 插件，并完成所需依赖安装和检查：
D:\Tools\webuse-claudecode
```

macOS 示例：

```text
请从这个本地路径中直接安装 WebUse 插件，并完成所需依赖安装和检查：
/Users/你的用户名/Tools/webuse-claudecode
```

如果 Claude Code 能够正常访问该目录，它可以读取项目中的插件配置、Skill 文件以及安装脚本，并按照项目提供的方式完成配置。

> 建议将项目放在一个长期不会移动的位置。后续如果移动或删除源文件夹，本地插件路径可能失效。

### 2.2 其它安装方式：直接以本地插件加载

Claude Code 支持直接从本地目录加载插件。进入终端后运行：

```text
claude --plugin-dir /absolute/path/to/webuse-claudecode
```

Windows 示例：

```text
claude --plugin-dir "D:\Tools\webuse-claudecode"
```

macOS 示例：

```text
claude --plugin-dir "/Users/你的用户名/Tools/webuse-claudecode"
```

### 2.3 手动安装运行依赖

WebUse 的 Python 运行环境不会直接安装在插件目录，而是安装到用户数据目录中。

默认位置：

- Windows：`%LOCALAPPDATA%\WebUse`
- macOS：`~/Library/Application Support/WebUse`

如果希望修改数据目录，可以提前设置环境变量：

```text
WEBUSE_DATA_DIR
```

#### Windows

在 PowerShell 中进入 `webuse-claudecode` 文件夹，然后运行：

```powershell
& '.\scripts\install.ps1'
```

安装脚本会创建独立 Python 虚拟环境、安装依赖，并自动执行一次环境检查。

#### macOS

在 Terminal 中进入 `webuse-claudecode` 文件夹，然后运行：

```bash
bash './scripts/install.sh'
```

安装完成后同样会自动执行一次环境检查。

---

## 三、安装后的检查与环境准备

### 3.0 最简单的检查方式

如果你不想阅读3.1-3.6中有关环境配置检查的要求
你也可以采用最简单的方式检查环境：
（在ClaudeCode中：
```text
请帮我检查webuse系列skill的运行环境是否正常；然后尝试启用其中的CDP打开浏览器，看看能否正常使用。
```

### 3.1 基础环境要求

建议准备以下环境：

- **Claude Code**
- **Python 3.10 或更高版本**
- **Google Chrome**，也可以使用项目能够识别的 Chromium / Edge
- Windows 建议使用原生 PowerShell，不建议借助 WSL 操作 Windows 桌面
- macOS 需要根据系统提示给实际执行 Claude Code / Python 的 Terminal、IDE 或宿主程序授予必要的屏幕与辅助功能权限

### 3.2 检查 Python

Windows：

```powershell
py -3 --version
```

或者：

```powershell
python --version
```

macOS：

```bash
python3 --version
```

版本应为 Python 3.10 或更高。

### 3.3 检查 WebUse 运行环境

当 WebUse 由 Claude Code 作为插件加载后，可以运行统一诊断。

Windows：

```powershell
& "$env:CLAUDE_PLUGIN_ROOT\scripts\webuse.ps1" doctor
```

macOS：

```bash
bash "$CLAUDE_PLUGIN_ROOT/scripts/webuse.sh" doctor
```

如果你是在项目源目录中手动检查，也可以直接执行对应安装脚本；安装脚本最后会自动运行 `doctor`。

检查时建议重点确认：

- Python 环境是否正常；
- Python 依赖是否已安装；
- Chrome / Chromium / Edge 是否能够找到；
- WebUse 数据目录是否可写；
- 桌面截图、鼠标等所需系统权限是否具备。

### 3.4 CDP 使用前需要准备 Chrome

WebUse **不会在压缩包内附带 Chrome 浏览器本体**。

如果要使用 CDP 模式，电脑上必须先安装：

- Google Chrome；或
- 项目能够识别的 Chromium / Microsoft Edge。

WebUse 会调用你电脑上已经安装的浏览器程序，并为 CDP 模式创建一个单独、持久化的浏览器 Profile。

Claude Code 版默认 CDP 地址为：

```text
http://127.0.0.1:9222
```

默认专用 Profile 位于 WebUse 数据目录中的：

```text
chrome-profile
```

### 3.5 启动 CDP 专用浏览器

在 Claude Code 插件环境中：

Windows：

```powershell
& "$env:CLAUDE_PLUGIN_ROOT\scripts\webuse.ps1" cdp launch --json
```

macOS：

```bash
bash "$CLAUDE_PLUGIN_ROOT/scripts/webuse.sh" cdp launch --json
```

第一次启动时会打开一个与日常 Chrome Profile 分离的 Chrome 窗口。

如果某个网站需要登录，请在这个专用浏览器中手动完成第一次登录。只要该 Profile 没有被删除或清理，后续通常可以继续保留登录状态。

### 3.6 检查 CDP 是否正常

Windows：

```powershell
& "$env:CLAUDE_PLUGIN_ROOT\scripts\webuse.ps1" cdp self-check --json
```

macOS：

```bash
bash "$CLAUDE_PLUGIN_ROOT/scripts/webuse.sh" cdp self-check --json
```

也可以进一步查看当前浏览器标签页：

Windows：

```powershell
& "$env:CLAUDE_PLUGIN_ROOT\scripts\webuse.ps1" cdp tabs --json
```

macOS：

```bash
bash "$CLAUDE_PLUGIN_ROOT/scripts/webuse.sh" cdp tabs --json
```

如果 `self-check` 能够正常连接，并且 `tabs` 能列出浏览器页面，说明 CDP 基本工作正常。

---

## 四、重要提示

### 1.目前，该项目支持两种使用模式：

#### 使用模式一：直接使用你平常使用的 Chrome

第一种方式是直接使用你的**原始 Chrome，也就是平常正在使用的那个 Chrome**。

由于 Chrome 官方的安全限制，WebUse 不应直接把你日常使用的默认浏览器 Profile 当作自己的远程调试 Profile，因此这种方式通常**无法使用 CDP 功能**。

尽管如此，WebUse 仍然支持桌面截图、视觉识别、鼠标点击和键盘操作，也就是说大部分普通网页任务仍然能够完成。

但是由于无法直接读取 DOM、选择器和页面内部状态，这种模式通常：

- 执行时间更长；
- 需要更多截图与状态确认；
- Token 消耗显著增加；
- 页面布局变化时稳定性可能低于 CDP 模式。

它最大的好处是：**使用的是你日常正在使用的 Chrome**。

因此已有网站登录态、Cookie 和常用会话通常可以直接使用。在很多情况下，你无需重新登录，也无需额外进行手动操作。

#### 使用模式二： 使用 Chrome 远程调试浏览器

第二种方式是使用 **Chrome 远程调试浏览器**，可以把它理解为一套供 WebUse / Claude Code 使用的专用浏览器环境。

需要注意，它并不是 Skill 压缩包内部自带了一份 Chrome，而是使用你电脑上已经安装的 Chrome / Chromium / Edge，并使用 WebUse 单独创建的持久化浏览器 Profile。

在这种方式下可以使用 CDP 功能，因此 Claude Code 可以更加直接地读取网页结构、定位元素、点击、输入、检查状态，任务执行通常会更加便捷和快速，Token 消耗也会明显降低。

该专用浏览器 Profile 默认会被持续保存在 WebUse 数据目录中。只要你没有主动删除 WebUse 数据、删除 `chrome-profile`，或者被系统清理软件、杀毒软件、磁盘清理工具等误删，该浏览器通常不会自动重置。

因此可以将它理解为一套长期保存的“Claude Code / WebUse 专用 Chrome Profile”：

- 第一次访问需要登录的网站时，通常需要你手动完成登录；
- 登录完成后，Session/Cookie 会保存在这个专用 Profile 中；
- 只要 Profile 没有被清理，第二次再使用同一个网站时通常无需重新登录。

出于安全考虑，请不要把正在运行的日常 Chrome Profile 直接复制给调试浏览器，也不要将包含登录状态的 `chrome-profile` 打包上传或分享给其他人。

另外，在某些 Claude Code 环境中，Claude 可能会选择使用 **Claude-in-Chrome** 来执行浏览器任务。Claude-in-Chrome 是 Anthropic 提供的另一套 Chrome 集成机制，与本项目 WebUse 不是同一个工具，其实际操作路径和效果也可能不同。

如果你希望任务明确由 WebUse 完成，请在提示词中明确写明：

```text
不要使用 Claude-in-Chrome。
```

这样可以尽量避免 Claude 在任务执行过程中改用其它浏览器控制方案。

### 2. 登录、验证码和敏感操作

遇到以下内容时，建议由你本人完成：

- 用户名/密码等敏感登录信息；
- MFA / 两步验证；
- CAPTCHA / 人机验证；
- 支付认证；
- 其它高敏感身份确认步骤。

完成后再告诉 Claude Code 继续任务即可。

### 3. 不要随意清理 WebUse 数据目录

WebUse 的浏览器登录状态和 Mem 记忆都保存在用户数据目录中。

默认：

- Windows：`%LOCALAPPDATA%\WebUse`
- macOS：`~/Library/Application Support/WebUse`

如果删除该目录，其中保存的专用 Chrome Profile、网站登录态和 Mem 记忆也可能一并消失。

---

## 五、推荐使用方式

### 如果希望使用模式一：直接操作日常 Chrome

建议在每次任务开始时使用下面的提示词：

```text
请使用 WebUse skills 完成任务，不要使用CDP或远程调试功能，直接使用我正在使用的chrome浏览器，不要使用Claude-in-Chrome。开始前读取相关 Mem 记忆，结束后记录可复用经验。任务是...
```

适合：

- 网站已经在你的日常 Chrome 中登录；
- 不希望重新登录专用浏览器；
- 任务操作步骤较少；
- 可以接受速度稍慢以及较高 Token 消耗。

### 如果希望使用模式二：使用 CDP 专用浏览器

建议使用：

```text
请使用 WebUse skills 完成任务，使用CDP远程调试功能并在调试版chrome中操作，不要使用Claude-in-Chrome。开始前读取相关 Mem 记忆，结束后记录可复用经验。任务是...
```

适合：

- 经常需要 Claude Code 操作网页；
- 希望任务执行更加快速、稳定；
- 页面操作较复杂；
- 希望减少截图识别次数和 Token 消耗；
- 愿意在第一次使用网站时在专用浏览器中手动登录一次。

对于长期使用，通常更推荐 **方式 2：CDP 专用浏览器**。完成常用网站第一次登录以后，它兼顾了执行速度、稳定性与持续登录状态。


---

## 六、使用建议

### 1. Claude Code 权限模式建议

Claude Code 提供多种权限模式。不同版本、套餐和组织策略下，可见的模式可能略有不同；在终端会话中通常可以使用 `Shift + Tab` 在当前可用的模式之间切换。

常见模式可以简单理解为：

1. **default / Manual（默认模式）**：最保守。读取文件通常可以直接进行，修改文件、执行命令或进行其它可能产生副作用的操作时，会较频繁地询问确认。
2. **acceptEdits（自动接受编辑）**：文件编辑通常可以自动放行，但执行 Shell 命令等操作仍可能要求确认。
3. **plan（计划模式）**：以分析和制定方案为主，适合先让 Claude 阅读项目、梳理步骤，再决定是否执行实际修改。
4. **auto（自动模式）**：尽量减少常规权限询问，由安全审核机制在操作执行前判断是否允许。是否可用取决于 Claude Code 版本、账号/套餐以及组织管理员设置。
5. **bypassPermissions（跳过权限）**：几乎跳过常规权限确认，自动化程度最高，但风险也最高。建议只在容器、虚拟机、临时 CI 等完全隔离且没有重要数据的环境中使用，不建议在日常电脑上开启。

WebUse 往往需要连续启动浏览器、读取页面状态、执行命令和进行多步操作。如果使用默认模式，任务过程中可能频繁出现确认提示，影响自动化体验。

**在你的账号和 Claude Code 版本支持的情况下，日常使用 WebUse 更推荐 `auto` 模式。** 它通常能够明显减少中途确认，同时仍保留额外的安全审核。涉及高风险、不可逆或敏感操作时，仍建议人工检查后再继续。

> 提示：权限模式属于 Claude Code 自身功能，不是 WebUse 提供的功能。不同版本的界面名称和可切换范围可能发生变化，请以当前 Claude Code 显示为准。

### 2. 可以用以下任务快速体验 WebUse

第一次体验时，建议优先使用 **CDP 专用浏览器模式**。如果网站尚未登录，请在 WebUse 打开的调试版 Chrome 中手动完成一次登录，然后再让 Claude Code 继续。

#### 示例 1：Gmail 邮件撰写与发送

将收件人替换为你自己的测试邮箱：

```text
请使用 WebUse skills 完成任务，使用CDP远程调试功能并在调试版chrome中操作，不要使用Claude-in-chrome。开始前读取相关 Mem 记忆，结束后记录可复用经验。

任务：在 Chrome 中打开 Gmail，给 ???@???.com 发送一封邮件。主题为 Sorry，正文请帮我撰写，约 200 字，大意是：很抱歉我错过了晚餐，因为会议延迟了；我想明天邀请对方一起吃晚餐。
```

#### 示例 2：Gmail 邀请邮件

```text
请使用 WebUse skills 完成任务，使用CDP远程调试功能并在调试版chrome中操作，不要使用Claude-in-chrome。开始前读取相关 Mem 记忆，结束后记录可复用经验。

任务：在 Chrome 中打开 Gmail，给 ???@???.com 发送一封邮件。主题为 Hello，正文请帮我撰写，约 200 字，大意是：昨天见到你很高兴，想邀请你今天晚上 22:00 一起吃宵夜。
```

> 邮件发送属于对外产生实际影响的操作。第一次测试时，建议使用你自己的备用邮箱作为收件人，并在发送前检查收件人、主题和正文。

#### 示例 3：知乎检索、总结并保存到桌面

```text
请使用 WebUse skills 完成任务，使用CDP远程调试功能并在调试版chrome中操作，不要使用Claude-in-chrome。开始前读取相关 Mem 记忆，结束后记录可复用经验。

任务：在 Chrome 中打开知乎，搜索“Claude Code 使用技巧”相关帖子，选择一个赞同数高于 100 的帖子，阅读并总结主要内容为一段文字，然后保存到桌面文件 Answer.txt。
```

#### 示例 4：知乎指定主题检索与文件保存

```text
请使用 WebUse skills 完成任务，使用CDP远程调试功能并在调试版chrome中操作，不要使用Claude-in-chrome。开始前读取相关 Mem 记忆，结束后记录可复用经验。

任务：在 Chrome 中打开知乎，搜索“Codex 的前世今生”相关帖子，打开搜索结果中的第一个相关帖子，阅读并总结主要内容为一段文字，然后保存到桌面文件 Answer.txt。
```

这些示例分别覆盖了网页打开、登录态复用、CDP 页面控制、表单填写、网页搜索、内容读取、Mem 记忆以及本地文件写入等能力，适合作为安装完成后的基础体验任务。
