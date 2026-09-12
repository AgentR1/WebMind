# 安全策略

## 支持范围

仅当前最新版本接受安全修复。项目只面向原生 Windows 上的 Codex；WSL、云端容器、远程控制另一台电脑及绕过宿主安全策略的用法不在支持范围内。

## 私下报告漏洞

请优先使用 GitHub 仓库的 **Security → Report a vulnerability** 私密报告功能。仓库维护者应在发布前启用 GitHub Private Vulnerability Reporting。

报告中请包含受影响版本、复现条件、预期与实际结果及影响范围。请使用合成数据，删除用户名、绝对路径、Cookie、令牌、Profile、截图和账号信息。

如果私密报告入口不可用，请仅创建一个不含利用细节和敏感数据的公开 Issue，要求维护者提供私密联系渠道。

## 不应公开提交的内容

- 密码、验证码、API Key、Cookie、会话标识、私钥或支付信息
- 活动 Mem、`mem-location.json`、`webmind-profile.json` 或任何 `*-Profile` 目录
- 登录、MFA、CAPTCHA、账号恢复或付款页面截图
- 能识别个人或组织的文件路径、日志、页面内容和账号数据

收到报告后，维护者应先确认影响和支持版本，再通过安全公告协调修复与披露。请不要为了复现而关闭沙箱、系统防护、Profile 核验或 failsafe。
