# 故障排除

[English](troubleshooting.md)

## 启动问题

### 端口已被占用

```
Error: Port 8000 is already in use
```

**解决方案：**
```bash
# 查找并终止进程
lsof -ti :8000 | xargs kill   # macOS/Linux
# 或使用停止脚本
bash scripts/stop-local.sh
```

### Python 版本太旧

```
ERROR: Python 3.10+ is required
```

**解决方案：** 从 [python.org](https://www.python.org/downloads/) 安装 Python 3.10 或更高版本。

### Node.js 版本太旧

```
ERROR: Node.js 18+ is required
```

**解决方案：** 从 [nodejs.org](https://nodejs.org/) 安装 Node.js 18+。

### 虚拟环境激活失败

```
source: command not found
```

**解决方案：** 使用对应 shell 的激活命令：
```bash
source .venv/bin/activate      # bash/zsh
.venv/Scripts/activate         # Windows cmd
.venv/Scripts/Activate.ps1     # Windows PowerShell
```

### pip 安装编译失败

**解决方案：** 安装构建工具：
```bash
# macOS
xcode-select --install

# Ubuntu/Debian
sudo apt-get install build-essential python3-dev

# Windows
# 安装 Visual C++ Build Tools
```

---

## Docker 问题

### 找不到 Docker Compose

```
docker: 'compose' is not a docker command
```

**解决方案：** 安装 Docker Compose v2：
```bash
docker compose version

# 参见：https://docs.docker.com/compose/install/
```

### 构建因内存不足失败

**解决方案：** 在 Docker Desktop 设置中增加内存分配（推荐 4 GB+）。

### 容器健康检查失败

```
backend  | unhealthy
```

**解决方案：** 检查后端日志：
```bash
docker compose logs backend
```

常见原因：
- requirements.txt 缺少依赖
- 数据库初始化错误
- 容器内端口冲突

---

## 运行时问题

### 浏览器控制台 CORS 错误

```
Access to fetch has been blocked by CORS policy
```

**解决方案：** 设置 CORS 源匹配前端 URL：
```bash
export ECOPILOT_CORS_ORIGINS='["http://localhost:3000"]'
```

### 上传失败 "文件太大"

**解决方案：** 增大上传限制：
```bash
export ECOPILOT_MAX_UPLOAD_SIZE_BYTES=104857600  # 100 MB
```

### 数据画像显示"结构未知"

当数据没有明确的面板、时间序列或横截面模式时会发生。

**解决方案：** 系统仍然可用 — 默认使用 OLS。您可以手动分配变量角色。

### Hausman 检验不可用

Hausman 检验需要固定效应和随机效应都收敛。近奇异协方差矩阵可能阻止计算。

**解决方案：** 对于小样本或高度共线性数据，这是预期行为。系统透明报告"不可用"。根据经济理论选择 FE 或 RE。

### 双向固定效应吸收主变量

当主解释变量与实体或时间虚拟变量共线时，双向固定效应会吸收它。

**解决方案：** 系统会对此发出警告。考虑使用单向固定效应，或重新考虑变量设定。

### PDF 导出返回 501

PDF 导出是已记录的占位功能，需要原生 Pango/Cairo 库。

**解决方案：** 使用 DOCX 或 LaTeX 导出替代。两者均完全可用。

---

## 数据问题

### Excel 文件无法上传

**解决方案：** 确保文件扩展名为 `.xlsx` 或 `.xls`。系统使用 `openpyxl` 处理 `.xlsx`，`xlrd` 处理 `.xls`。

### 未检测到缺失值

**解决方案：** 确保缺失值编码为空单元格、`NA`、`NaN` 或 `None`。自定义编码（如 `-999`、`N/A`）不会自动检测。

### 列类型检测错误

类型推断基于规则，可能错误分类。

**解决方案：** 您可以在模型配置步骤中覆盖变量角色。类型检测不会阻止任何分析。

---

## 前端问题

### 页面空白或一直加载

**解决方案：**
1. 检查后端是否运行（`curl http://localhost:8000/health`）
2. 检查浏览器控制台错误（F12 → Console）
3. 确认 `NEXT_PUBLIC_API_BASE_URL` 指向后端

### 构建时 TypeScript 错误

**解决方案：**
```bash
cd frontend
npx tsc --noEmit  # 显示所有类型错误
```

---

## 获取帮助

- 查看 [API 文档](http://localhost:8000/docs)（Swagger UI）
- 查阅 [架构文档](architecture.md)
- 在项目仓库提交 issue
