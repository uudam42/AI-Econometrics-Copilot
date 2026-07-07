# 快速开始指南

[English](quickstart.md)

## 方式一：Docker（推荐）

```bash
git clone https://github.com/your-org/ai-econometrics-copilot.git
cd ai-econometrics-copilot
docker compose up --build
```

打开 [http://localhost:3000](http://localhost:3000)。完成。

## 方式二：本地开发

### 环境要求

- Python 3.10+（`python --version`）
- Node.js 18+（`node --version`）

### 自动化

```bash
bash scripts/start-local.sh
```

脚本会检查依赖、创建虚拟环境、安装包、启动两个服务并打开浏览器。

### 手动

**后端：**
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**前端：**
```bash
cd frontend
npm install
npm run dev
```

## 第一步

1. 打开 [http://localhost:3000](http://localhost:3000)
2. 点击 **试用样本数据集** 创建一个预加载世界银行面板数据的演示项目
3. 数据集自动画像 — 查看面板结构（20 个国家，15 年）
4. 点击 **配置并运行模型** 设置第一次回归
5. 变量角色已预填充；选择固定效应并点击 **运行分析**
6. 查看系数表、诊断检验和残差图
7. 尝试 **比较模型** 同时运行多个规格

## 停止应用

```bash
bash scripts/stop-local.sh       # macOS / Linux
powershell scripts/stop-local.ps1  # Windows
```

Docker：
```bash
docker compose down
```

## 重置数据

```bash
bash scripts/reset-local-data.sh       # 本地
docker compose down -v                 # Docker
```

## 方式三：Windows 桌面应用

从 Releases 下载安装程序。无需 Docker、Python 或 Node.js。

1. 运行安装程序（`.msi` 或 `Setup.exe`）
2. 从开始菜单打开 **AI Econometrics Copilot**
3. 应用自动启动 — 无需额外设置
4. 所有数据存储在本地 `%LOCALAPPDATA%\AI Econometrics Copilot\`

注意：未签名构建可能触发 Windows SmartScreen 警告。点击"更多信息"→"仍要运行"。

## 下一步

- [用户指南](user-guide.zh-CN.md) — 完整功能介绍
- [故障排除](troubleshooting.zh-CN.md) — 常见问题与解决方案
- [部署指南](deployment.zh-CN.md) — 生产环境部署
