# 部署指南

[English](deployment.md)

## 概述

AI 计量经济学助手设计用于单用户本地部署。本指南涵盖 Docker 部署、反向代理配置和生产环境注意事项。

---

## Docker 部署

### 基础

```bash
docker compose up --build -d
```

启动：
- **后端** 端口 8000（FastAPI + Uvicorn）
- **前端** 端口 3000（Next.js）
- 数据持久化到 `ai_econometrics_data` 命名卷

### 自定义端口

编辑 `docker-compose.yml`：
```yaml
services:
  backend:
    ports:
      - "9000:8000"
  frontend:
    ports:
      - "4000:3000"
    environment:
      - NEXT_PUBLIC_API_BASE_URL=http://localhost:9000/api
```

### 健康检查

两个服务都包含 Docker 健康检查：
- 后端：`python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"`
- 前端：`node -e "require('http').get('http://localhost:3000', r => process.exit(r.statusCode === 200 ? 0 : 1))"`

前端等待后端健康后再启动。

### 卷管理

```bash
# 查看数据卷
docker volume inspect ai_econometrics_data

# 备份
docker run --rm -v ai_econometrics_data:/data -v $(pwd):/backup alpine \
  tar czf /backup/econometrics_backup.tar.gz -C /data .

# 恢复
docker run --rm -v ai_econometrics_data:/data -v $(pwd):/backup alpine \
  tar xzf /backup/econometrics_backup.tar.gz -C /data

# 重置
docker compose down -v
```

---

## 反向代理（Nginx）

通过单一域名提供两个服务的 Nginx 配置示例：

```nginx
server {
    listen 80;
    server_name econometrics.example.com;

    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /api/ {
        proxy_pass http://localhost:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        client_max_body_size 50m;
    }

    location /docs {
        proxy_pass http://localhost:8000/docs;
    }

    location /health {
        proxy_pass http://localhost:8000/health;
    }
}
```

更新环境变量：
```bash
ECOPILOT_CORS_ORIGINS='["https://econometrics.example.com"]'
NEXT_PUBLIC_API_BASE_URL=https://econometrics.example.com/api
```

---

## 环境变量

所有后端变量使用 `ECOPILOT_` 前缀。完整列表见 [`.env.example`](../.env.example)。

关键生产设置：

| 变量 | 生产值 | 用途 |
|---|---|---|
| `ECOPILOT_LOG_LEVEL` | `WARNING` | 减少日志详细度 |
| `ECOPILOT_CORS_ORIGINS` | `["https://your-domain.com"]` | 限制 CORS |
| `ECOPILOT_MAX_UPLOAD_SIZE_BYTES` | 按需调整 | 上传限制 |

---

## 数据持久化

### SQLite

默认数据库为 SQLite，存储在 `data/ai_econometrics.db`。适合单用户部署。多用户场景（当前不支持）可考虑 PostgreSQL。

### 文件存储

- 上传的数据集：`data/uploads/`
- 生成的档案：`data/artifacts/`

两个目录在启动时自动创建。

### 备份策略

```bash
# 停止服务
docker compose stop

# 备份整个数据目录
tar czf backup_$(date +%Y%m%d).tar.gz -C backend data/

# 重启
docker compose start
```

---

## 生产环境注意事项

### 本平台是

- 单用户研究工具
- 本地优先，无云依赖
- 面向学术和研究使用

### 本平台不是

- 非多用户 SaaS 应用
- 无内置身份认证或授权
- 无云同步或协作功能
- 非高并发工作负载设计

### 安全注意事项

- 未内置认证 — 不要在没有反向代理和认证层的情况下暴露到公网
- SQLite 不支持并发写入 — 仅限单用户
- 文件上传按扩展名和大小验证，但不扫描恶意软件
- CORS 可配置 — 在生产环境中限制为您的域名

### 性能

- SQLite 对典型研究数据集处理良好（约 100 万行以内）
- DataFrame 首次加载后缓存在内存中
- 应用可干净重启 — 缓存数据从磁盘重新加载
- 内存使用随数据集大小扩展；推荐 4 GB RAM

---

## 更新

```bash
git pull
docker compose up --build -d
```

命名卷中的数据在重建后保留。

---

## Windows 桌面分发

无需 Docker 或任何运行时依赖的独立 Windows 部署：

### 构建安装程序

前置条件（仅开发机器）：
- Rust（`rustup default stable`）
- Node.js 18+
- Python 3.10+

```powershell
.\desktop\scripts\build-desktop.ps1
```

输出：`desktop/src-tauri/target/release/bundle/msi/` 和 `nsis/`

### 终端用户安装

1. 下载安装程序（`.msi` 或 `Setup.exe`）
2. 运行安装程序
3. 从开始菜单打开

无需 Docker、Python、Node.js 或浏览器。

### 桌面数据位置

用户数据存储在 `%LOCALAPPDATA%\AI Econometrics Copilot\`：
- `database/` — SQLite 数据库（升级后保留）
- `uploads/`、`artifacts/`、`exports/` — 用户文件
- `logs/` — 应用日志

卸载不会删除用户数据。

### 已知限制

- 仅限 Windows（macOS 和 Linux 桌面包尚未构建）
- 未签名构建 — 预计出现 Windows SmartScreen 警告
- 无自动更新
- 无云同步
