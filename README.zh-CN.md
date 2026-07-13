[English](README.md)

# AI 计量经济学助手

一个可解释、可复现的计量经济建模平台，面向经济学研究。
AI 负责理解与推荐 — Python 统计库执行所有实际计算 — 用户保留最终研究判断权。

> **核心原则：** LLM 不会生成回归系数、p 值、R² 或显著性结论。所有统计数值由 `statsmodels`、`linearmodels`、`pandas`、`numpy` 和 `scipy` 计算。

---

## 快速开始

### Docker 一键启动

```bash
docker compose up --build
```

打开 [http://localhost:3000](http://localhost:3000)。后端 API 文档见 [http://localhost:8000/docs](http://localhost:8000/docs)。

数据存储在 Docker 命名卷 (`ai_econometrics_data`) 中。重置数据：

```bash
docker compose down -v
```

### 本地开发

```bash
bash scripts/start-local.sh       # macOS / Linux
powershell scripts/start-local.ps1  # Windows
```

使用 Make：

```bash
make start    # 启动两个服务
make stop     # 停止两个服务
make test     # 运行后端测试 + 前端 lint + 类型检查
```

### 手动设置

**后端：**
```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**前端：**
```bash
cd frontend
npm install
npm run dev
```

打开 [http://localhost:3000](http://localhost:3000)。

---

## 环境要求

- Python 3.10+（推荐 3.12）
- Node.js 18+（推荐 20）
- Docker + Docker Compose（一键启动需要）

---

## 核心功能

| 功能 | 说明 |
|---|---|
| 数据上传 | CSV、Excel (.xlsx/.xls)，最大 50 MB |
| 数据画像 | 缺失值、异常值、偏度、转换建议 |
| 结构检测 | 面板 / 时间序列 / 横截面（基于规则，非仅列名） |
| 变量角色选择 | 因变量、主解释变量、控制变量、实体 ID、时间 — 规则预填充 |
| 数据转换 | 对数化、缩尾、标准化、插补、删除重复/缺失 |
| OLS 回归 | 普通与 HC1 稳健标准误（`statsmodels`） |
| 面板回归 | 混合 OLS、固定效应、随机效应、双向固定效应（`linearmodels`） |
| 聚类标准误 | 按实体聚类的面板模型标准误 |
| 诊断检验 | VIF、Breusch-Pagan、Jarque-Bera、Durbin-Watson、Hausman 检验 |
| 多模型比较 | 同一变量集最多 6 个模型并排比较 |
| 透明推荐 | 多准则评分（结构、Hausman、异方差、简约性、拟合度） |
| 系数稳定性 | 跨规格比较主解释变量系数 |
| 研究报告 | 确定性叙述生成 — 不含 LLM、不含虚构统计量 |
| 报告导出 | Markdown、HTML、JSON，含可复现元数据 |
| 研究规划 | 自然语言输入研究问题 → 建议变量、模型、转换 |
| 因果语言检测 | 检测 "cause/affect/impact" 并重新表述为关联性 |
| 吸收变量透明化 | 双向固定效应报告被吸收的变量 |
| 探索性发现 | 有界规格搜索，多重检验校正（BH/Bonferroni） |
| 发现→计划衔接 | 一键将探索性发现提升为研究计划 |
| 持久化工作空间 | SQLite 支持的项目，重启不丢失 |
| 时间线追踪 | 每个项目操作的时间顺序记录 |
| 出版级表格 | 带 *** 显著性标记的学术回归表 |
| 学术图表 | 系数图、残差图、拟合值图、相关热力图、稳定性图 |
| DOCX 导出 | 可编辑 Word 文档，含封面、表格、图表 |
| LaTeX 导出 | 独立 .tex 文件，含 tables/、figures/、appendix/ |
| 方法论附录 | 自动生成方法论、变量选择、局限性 |
| 可复现附录 | 数据集校验和、转换日志、软件版本 |
| 演示项目 | 一键创建世界银行面板数据样本项目 |

---

## 架构

```
上传 → 画像 → 变量选择 → 转换 → 运行模型 → 结果
     ↘ 发现 → 筛选 → 规格 → 校正 → 发现 → 计划
     ↘ 项目工作空间 → 数据集 → 分析 → 时间线 → 导出包
```

**关注点分离：**
- `app/services/` — 纯数据函数（画像、结构检测、转换）
- `app/analysis/` — 统计计算封装（OLS、面板、诊断）
- `app/api/` — 轻量 HTTP 路由，无业务逻辑
- `app/schemas/` — 跨层共享的 Pydantic 模型
- `app/storage/` — SQLite 持久化 + 内存缓存
- `app/reports/` — 出版导出生成器（表格、图表、DOCX、LaTeX）

---

## 技术栈

**后端：**
- Python 3.12、FastAPI、Pydantic v2、pydantic-settings
- pandas、numpy、scipy
- statsmodels（OLS、诊断）、linearmodels（面板回归）
- SQLAlchemy 2.x（SQLite 持久化）
- python-docx（DOCX 导出）、matplotlib（图表）
- openpyxl（Excel 支持）
- pytest、httpx

**前端：**
- Next.js 16、React 19、TypeScript 5
- Tailwind CSS v4、Recharts v3
- lucide-react

**基础设施：**
- Docker、Docker Compose
- SQLite（基于文件，零配置）

---

## 仓库结构

```
ai-econometrics-copilot/
├── backend/
│   ├── app/
│   │   ├── analysis/       # OLS、面板模型、诊断、发现、推荐器
│   │   ├── api/            # REST 端点：数据集、分析、项目、引导
│   │   ├── core/           # 配置、错误、日志
│   │   ├── reports/        # 学术表格、图表、DOCX、LaTeX、附录
│   │   ├── schemas/        # Pydantic 模型
│   │   ├── services/       # 画像、结构检测、转换
│   │   └── storage/        # SQLite 模型、仓库、数据库引擎
│   ├── tests/              # 274 个测试
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── app/                # Next.js 页面
│   ├── components/         # UI 组件（建模、结果、项目、引导）
│   ├── lib/                # API 客户端、工具函数
│   ├── types/              # TypeScript 接口
│   ├── Dockerfile
│   └── package.json
├── sample_data/            # 世界银行面板样本数据集
├── scripts/                # 启动、停止、重置脚本 (sh + ps1)
├── docs/                   # 架构、API、计量规则、开发计划
├── docker-compose.yml
├── Makefile
└── .env.example
```

---

## 支持的模型

| 模型 | 库 | 适用场景 |
|---|---|---|
| OLS | statsmodels | 横截面 / 基准模型 |
| 稳健 OLS (HC1) | statsmodels | 异方差误差 |
| 混合 OLS | linearmodels | 面板数据，忽略面板结构 |
| 固定效应 | linearmodels | 时间不变的未观察异质性 |
| 随机效应 | linearmodels | 不相关的实体效应 |
| 双向固定效应 | linearmodels | 实体 + 时间效应 |

---

## 支持的诊断检验

| 诊断检验 | 用途 |
|---|---|
| VIF | 多重共线性检查（阈值：5 / 10） |
| Breusch-Pagan | 异方差检验 |
| Jarque-Bera | 残差正态性检验 |
| Durbin-Watson | 一阶自相关 |
| Hausman 检验 | 固定效应 vs 随机效应选择 |
| 相关矩阵 | Pearson 相关热力图 |
| 描述统计 | 各变量汇总 |

---

## 推荐评分标准

| 准则 | 权重 |
|---|---|
| 结构兼容性 | 25% |
| Hausman 检验指导 | 20% |
| 异方差稳健性 | 15% |
| 模型拟合度 | 15% |
| 简约性 | 10% |
| 样本量适当性 | 10% |
| 估计成功率 | 5% |

---

## 使用示例

1. 打开应用 — 首次用户看到工作流程引导卡片
2. 点击 **试用样本数据集** 创建含世界银行数据的演示项目
3. 查看数据画像 — 检测到面板结构（20 实体 × 15 期）
4. 点击 **配置并运行模型 →**
5. 变量角色已预填充：`gdp_per_capita` 为因变量，`internet_users` 为解释变量
6. 可选择对右偏变量应用对数转换
7. 选择 **固定效应**（面板数据推荐）
8. 启用按实体聚类的标准误
9. 点击 **运行分析 →**
10. 查看系数表、显著性星号、诊断检验、残差图
11. 通过 **比较模型** 对比不同规格
12. 生成研究报告或出版级导出（DOCX/LaTeX）
13. 导出可复现的 JSON 分析档案

---

## 环境变量

所有后端变量使用 `ECOPILOT_` 前缀。完整列表见 [`.env.example`](.env.example)。

| 变量 | 默认值 | 用途 |
|---|---|---|
| `ECOPILOT_DATABASE_URL` | `sqlite:///./data/ai_econometrics.db` | 数据库连接 |
| `ECOPILOT_DATA_DIR` | `data` | 基础数据目录 |
| `ECOPILOT_UPLOAD_DIR` | `data/uploads` | 上传文件存储 |
| `ECOPILOT_ARTIFACT_DIR` | `data/artifacts` | 生成物存储 |
| `ECOPILOT_CORS_ORIGINS` | `["http://localhost:3000"]` | 允许的 CORS 源 |
| `ECOPILOT_MAX_UPLOAD_SIZE_BYTES` | `52428800` (50 MB) | 上传大小限制 |
| `ECOPILOT_LOG_LEVEL` | `INFO` | 日志级别 |
| `NEXT_PUBLIC_API_BASE_URL` | `http://localhost:8000/api` | 前端 API 端点 |

---

## 运行测试

```bash
# 后端（274 个测试）
cd backend
source .venv/bin/activate
python -m pytest -q

# 前端类型检查 + lint
cd frontend
npx tsc --noEmit
npm run lint
npm run build
```

使用 Make：
```bash
make test
```

---

## Docker 部署

```bash
docker compose up --build -d
```

- 后端：端口 8000，带健康检查 (`/health`)
- 前端：端口 3000，带健康检查
- 数据持久化到 `ai_econometrics_data` 命名卷
- 前端等待后端健康后再启动

```bash
docker compose down      # 停止，保留数据
docker compose down -v   # 停止并删除所有数据
```

---

## 可复现设计

每次分析存储完整记录：
- 原始数据集元数据和 SHA-256 校验和
- 每个转换操作（含转换前后行数）
- 精确的模型公式和配置
- 所有系数、标准误、p 值和诊断检验
- 软件库版本和时间戳

通过 `GET /api/analyses/{id}/export/json` 导出，或作为项目 ZIP 包导出。

---

## 出版导出

从任意分析、比较或报告生成出版级文档：

- **DOCX** — Times New Roman 字体，格式化表格，嵌入图表，封面页
- **LaTeX** — 独立 .tex 文件，正确转义，可用 `pdflatex` 编译
- **Markdown** — 学术风格表格，含显著性星号
- **JSON** — 结构化档案，支持程序化访问

PDF 导出为已记录的占位功能 — DOCX 和 LaTeX 为完全可用的替代方案。

---

## Windows 独立桌面应用

提供独立的 Windows 桌面版本 — 无需 Docker、Python、Node.js 或浏览器。

**终端用户：**
1. 从 Releases 下载安装程序（`.msi` 或 `Setup.exe`）
2. 运行安装程序
3. 从开始菜单打开 **AI Econometrics Copilot**
4. 所有数据保存在本地 `%LOCALAPPDATA%\AI Econometrics Copilot\`

**开发者构建安装程序：**
```powershell
# 前置条件：Rust、Node.js 18+、Python 3.10+
.\desktop\scripts\build-desktop.ps1
```

详见 [`desktop/README.md`](desktop/README.md)。

**桌面技术：** Tauri 2.x + 内嵌 FastAPI sidecar (PyInstaller) + 静态 Next.js 前端。

**尚未提供：** macOS/Linux 桌面包、自动更新、代码签名。

---

## 快速分析

**快速分析**是一个四阶段引导式工作流，无需统计学背景，即可从原始数据文件直接获得完整的计量分析结果。

**使用方式：**
1. 在首页点击 **分析我的 Excel**（桌面版或浏览器版均可）
2. 上传 CSV 或 Excel 文件，并可选填研究问题
3. 审核系统自动生成的分析方案（推荐模型、因变量、自变量）
4. 确认后运行分析，查看结果和通俗解读

**系统将自动完成：**
- 检测数据结构（面板 / 截面 / 时间序列）
- 推荐合适的模型（OLS、固定效应、随机效应、对数 OLS）
- 生成不含技术术语的通俗解读
- 计算诊断统计量（VIF、Breusch-Pagan、Jarque-Bera）

**注意：** 快速分析提供的是相关分析。如需因果推断，请使用高级工作流（项目）。

详细文档见 [`docs/quick-analyze.zh-CN.md`](docs/quick-analyze.zh-CN.md)。

---

## 当前局限

- 单用户本地 SQLite 存储 — 无多用户或云同步
- 无身份认证或权限控制
- 无任意公式编辑器（变量通过 UI 选择）
- PDF 导出需要原生 Pango/Cairo 库 — DOCX 和 LaTeX 可作为替代
- Hausman 检验使用伪逆矩阵 — 近奇异矩阵可能报告不可用
- 双向固定效应可能吸收与实体/时间虚拟变量共线的变量（已透明报告）
- Windows 桌面构建未签名 — 预计会出现 SmartScreen 警告

---

## 路线图

| 阶段 | 功能 | 状态 |
|---|---|---|
| 阶段 1 | 数据上传、画像、结构检测 | 完成 |
| 阶段 2 | 变量配置、数据转换 | 完成 |
| 阶段 3 | 回归执行、计量诊断 | 完成 |
| 阶段 4 | 多模型比较、推荐、报告 | 完成 |
| 阶段 5 | 研究规划、吸收变量透明化 | 完成 |
| 阶段 6 | 有约束探索性关系发现 | 完成 |
| 阶段 7 | 持久化研究工作空间 | 完成 |
| 阶段 8 | 出版级报告与学术导出 | 完成 |
| 阶段 9 | 引导体验、一键启动、文档 | 完成 |
| 阶段 10 | Windows 独立桌面应用 | 完成 |
| 阶段 11 | 快速分析、桌面打磨与文档完善 | 进行中 |
| 阶段 12 | 高级计量模型与因果识别工作流 | 未来 |

---

## 因果语言免责声明

> 本分析识别统计关联性，不确立因果效应，除非额外的识别假设已被证明合理。

---

## 许可证

MIT
