# Windows 安装指南

[English version](windows-installation.md)

本指南介绍如何在 Windows 10 和 Windows 11 上安装 AI Econometrics Copilot 桌面版。

---

## 系统要求

| 组件 | 最低要求 | 推荐配置 |
|------|---------|---------|
| 操作系统 | Windows 10（64 位，版本 1903 及以上） | Windows 11 |
| 内存 | 4 GB | 8 GB |
| 磁盘空间 | 500 MB 可用空间 | 2 GB 可用空间 |
| WebView2 | 必须安装 | 必须安装 |
| 网络连接 | 安装后不需要 | 不需要 |

---

## 第一步 — 检查 WebView2

AI Econometrics Copilot 需要 **Microsoft Edge WebView2 运行时**。

- **Windows 11**：WebView2 已预装，无需额外安装。
- **Windows 10**：可能需要手动安装。

检查是否已安装 WebView2：
1. 打开 **设置 → 应用 → 已安装的应用**
2. 搜索"WebView2"
3. 若显示"Microsoft Edge WebView2 Runtime"，则可以继续

如未安装，请从以下地址下载：
**https://developer.microsoft.com/zh-cn/microsoft-edge/webview2/**

选择 **常青版独立安装程序 (x64)**，下载后运行即可。

---

## 第二步 — 下载安装包

从 GitHub Releases 页面下载最新版本：

**https://github.com/uudam42/ai-econometrics-copilot/releases/latest**

提供两种安装格式：

| 文件 | 格式 | 适用场景 |
|------|------|---------|
| `AI.Econometrics.Copilot_x.x.x_x64_en-US.msi` | MSI | 企业/IT 批量部署 |
| `AI.Econometrics.Copilot_x.x.x_x64-setup.exe` | NSIS | 个人/家庭使用 |

个人用户建议下载 `.exe` 安装程序。

下载后，使用与安装包同一页面发布的 `checksums.sha256` 文件验证 SHA256 校验值：

```powershell
(Get-FileHash "AI.Econometrics.Copilot_x.x.x_x64-setup.exe" -Algorithm SHA256).Hash.ToLower()
# 将输出结果与 checksums.sha256 中的值对比
```

---

## 第三步 — 运行安装程序

### NSIS 安装程序（Setup.exe）

1. 双击下载的 `*-setup.exe`
2. 若 Windows 智能屏幕显示警告，点击 **更多信息 → 仍要运行**
   （此版本安装包暂未进行代码签名，因此会触发该警告。）
3. 按照安装向导完成安装
4. 程序将安装至 `C:\Users\<用户名>\AppData\Local\AI Econometrics Copilot\`

### MSI 安装程序

```powershell
msiexec /i "AI.Econometrics.Copilot_x.x.x_x64_en-US.msi" /qn
```

或双击 `.msi` 文件，按向导完成安装。

---

## 第四步 — 启动应用

安装完成后，通过以下方式启动 AI Econometrics Copilot：
- **开始菜单 → AI Econometrics Copilot**
- **桌面快捷方式**（安装时选择创建）

首次启动时，应用会显示启动画面，同时初始化后端分析引擎（通常需要 3–8 秒）。

---

## 安装内容

| 组件 | 位置 |
|------|------|
| 应用程序文件 | `%LOCALAPPDATA%\AI Econometrics Copilot\` |
| 开始菜单快捷方式 | `%APPDATA%\Microsoft\Windows\Start Menu\Programs\` |
| 用户数据 | `%LOCALAPPDATA%\AI Econometrics Copilot\`（首次运行时创建） |

安装程序**不会**修改系统级设置、用户注册表之外的注册表项，也不会安装任何系统服务。

---

## 卸载

**通过设置卸载：**
1. 打开 **设置 → 应用 → 已安装的应用**
2. 搜索"AI Econometrics Copilot"
3. 点击 **卸载**

**通过控制面板卸载：**
1. 打开 **控制面板 → 程序 → 卸载程序**
2. 选择 **AI Econometrics Copilot**
3. 点击 **卸载**

卸载程序**不会**删除 `%LOCALAPPDATA%\AI Econometrics Copilot\` 中的用户数据（数据库、上传文件、导出文件）。如需彻底清除，请手动删除该文件夹。

---

## 防火墙与网络

应用仅在本地随机端口绑定 HTTP 服务（`127.0.0.1`，不对外），不发起任何入站或出站互联网连接。若防火墙提示权限申请，请选择**拒绝**外部访问——本地端口仅用于 Tauri 外壳与后端之间的进程间通信。

---

## 防病毒软件与智能屏幕

由于当前版本安装包暂未进行代码签名，Windows 智能屏幕和部分防病毒软件可能会发出警告，这属于正常现象。运行前建议使用 SHA256 校验值（第二步）验证文件完整性。

若防病毒软件隔离了安装程序：
1. 核实 SHA256 校验值与发布值一致
2. 为安装程序及应用目录添加白名单例外

---

## 安装问题排查

**出现"Windows 已保护你的电脑"（智能屏幕）**
点击 **更多信息 → 仍要运行**。由于当前版本暂未签名，此提示属正常现象。

**提示"此应用无法在你的电脑上运行"**
请确认已下载 `x64` 版本安装包，且 Windows 为 64 位系统。

**安装后应用无法启动**
请确认 WebView2 已安装（第一步）。更多诊断步骤请参见 [Windows 验证指南](windows-verification.zh-CN.md)。

**安装过程卡住或失败**
请尝试以管理员身份运行安装程序：右键点击安装程序 → **以管理员身份运行**。
