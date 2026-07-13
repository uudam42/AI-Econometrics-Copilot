# Windows 验证指南

[English version](windows-verification.md)

使用本指南验证安装后 AI Econometrics Copilot 是否正常运行，或诊断启动失败的原因。

---

## 快速验证清单

启动应用后，逐项确认以下内容：

- [ ] 启动画面出现，并显示进度指示器
- [ ] 进度指示器依次经过四个阶段
- [ ] 主界面在 15 秒内加载完成
- [ ] 首页显示"AI Econometrics Copilot"及三张操作卡片
- [ ] 点击"分析我的 Excel"能跳转至快速分析页面
- [ ] 文件上传正常（可用 `sample_data/world_bank_panel_sample.xlsx` 测试）

若任意项未通过，请参阅下方对应的诊断章节。

---

## 启动阶段说明

应用显示四个启动阶段，每个阶段应在数秒内完成：

| 阶段 | 界面提示文字 | 执行内容 |
|------|------------|---------|
| 1 | 正在准备本地工作区… | 创建数据目录 |
| 2 | 正在启动分析引擎… | 启动后端子进程 |
| 3 | 正在加载研究工具… | 等待后端健康检查响应 |
| 4 | 就绪 | 前端加载完成 |

若应用显示 **无法启动**，则启动失败。请参见下方[从启动失败中恢复](#从启动失败中恢复)章节。

---

## 手动验证后端健康状态

打开 PowerShell 运行：

```powershell
# 查找后端进程
$proc = Get-Process "ai-econometrics-backend" -ErrorAction SilentlyContinue
if ($proc) {
    Write-Host "后端进程正在运行（PID: $($proc.Id)）"
} else {
    Write-Host "未找到后端进程"
}
```

若后端在运行但应用仍启动失败，请查看日志文件：

```powershell
$logPath = "$env:LOCALAPPDATA\AI Econometrics Copilot\logs\backend.log"
if (Test-Path $logPath) {
    Get-Content $logPath -Tail 50
} else {
    Write-Host "日志文件不存在：$logPath"
}
```

---

## 验证文件结构

首次启动后，以下目录应已存在：

```powershell
$base = "$env:LOCALAPPDATA\AI Econometrics Copilot"
foreach ($sub in @("database", "uploads", "artifacts", "exports", "logs", "config")) {
    $path = Join-Path $base $sub
    if (Test-Path $path) {
        Write-Host "[正常] $path"
    } else {
        Write-Host "[缺失] $path"
    }
}
```

六个子目录应全部显示 `[正常]`。若有目录缺失，可能是权限问题。

---

## 验证 WebView2

```powershell
$webview2 = Get-ItemProperty `
  "HKLM:\SOFTWARE\WOW6432Node\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}" `
  -ErrorAction SilentlyContinue
if ($webview2) {
    Write-Host "WebView2 版本：$($webview2.pv)"
} else {
    Write-Host "未找到 WebView2，请从以下地址安装：https://developer.microsoft.com/zh-cn/microsoft-edge/webview2/"
}
```

---

## 快速分析端到端测试

1. 启动应用
2. 在首页点击 **分析我的 Excel**
3. 点击 **选择文件**，选择 `sample_data/world_bank_panel_sample.xlsx`
4. 研究问题可留空，点击 **上传并分析**
5. 等待规划阶段完成（数秒）
6. 查看分析方案，点击 **确认并运行分析**
7. 确认结果页面正常显示，包括通俗解读和诊断统计表

若任一步骤失败，请记录失败阶段并参阅下方[问题排查](#问题排查)章节。

---

## 从启动失败中恢复

应用显示红色"无法启动"面板时，请按以下步骤操作：

### 1. 阅读错误信息

"无法启动"下方的错误信息描述了具体失败原因。

### 2. 复制技术详情

点击 **复制技术详情**，将 JSON 诊断信息复制到剪贴板，粘贴至文本编辑器或问题反馈表单。

### 3. 查看日志

点击 **打开日志文件夹**，在文件管理器中打开 `%LOCALAPPDATA%\AI Econometrics Copilot\logs\`。用文本编辑器打开 `backend.log`，查看文件末尾的错误信息。

### 4. 常见启动失败原因

| 症状 | 可能原因 | 解决方法 |
|------|---------|---------|
| "无法启动分析引擎" | 找不到子进程可执行文件 | 重新安装应用 |
| "分析引擎未在规定时间内响应" | 端口冲突或机器较慢 | 点击重试；若持续出现，请重启电脑 |
| 应用立即崩溃 | WebView2 缺失 | 安装 WebView2（参见[安装指南](windows-installation.zh-CN.md)） |
| 白屏 | 前端静态文件缺失 | 重新安装应用 |

### 5. 重置本地数据

若数据库损坏：
1. 导航至 `%LOCALAPPDATA%\AI Econometrics Copilot\`
2. 删除 `database\` 文件夹
3. 重启应用（数据库将自动重建）

也可点击恢复面板中的 **打开数据文件夹** 按钮直接导航至该目录。

### 6. 重试

点击 **重试** 按钮，无需关闭窗口即可重新加载应用。

### 7. 关闭并重新打开

点击 **关闭应用** 以安全方式退出，然后从开始菜单重新打开。

---

## 问题排查

**应用窗口空白/白屏**
- 重新安装应用（前端静态文件可能缺失）
- 确认 WebView2 已安装且为最新版本

**应用打开但显示"连接被拒绝"错误**
- 后端可能未能启动，请查看 `backend.log`
- 尝试重启应用

**文件上传失败，提示"网络错误"**
- 后端可能在启动后崩溃，请查看 `backend.log`
- 点击重试或重启应用

**分析结果为空**
- 确认数据集至少有两列数值型变量
- 可用 `sample_data/world_bank_panel_sample.xlsx` 测试，排除数据集问题

**应用响应非常缓慢**
- 在旧机器上，后端冷启动可能需要最长 30 秒
- 请耐心等待启动画面，不要过早判断为失败

---

## 提交问题反馈

提交 Bug 时请包含以下信息：

1. Windows 版本（运行 `winver` 查看）
2. **复制技术详情** 导出的 JSON 内容
3. `%LOCALAPPDATA%\AI Econometrics Copilot\logs\backend.log` 末尾 50 行内容
4. 复现步骤

请在此提交问题：**https://github.com/uudam42/ai-econometrics-copilot/issues**
