[English](README.md)

# AI Econometrics Copilot（AI 计量建模助手）

面向经济学研究的可解释、可复现计量建模平台。
AI 负责理解、推荐和解释——Python 统计库执行全部真实计算——用户保留最终的研究判断权。

> **核心原则：** 大语言模型绝不生成回归系数、p 值、R²或显著性结论。所有统计数值均由 `statsmodels`、`linearmodels`、`pandas`、`numpy` 和 `scipy` 计算。

---

## 核心功能

| 功能 | 说明 |
|---|---|
| 数据集上传 | 支持 CSV、Excel（.xlsx/.xls），最大 50 MB |
| 数据剖析 | 缺失值、异常值、偏度分析，变换建议 |
| 结构检测 | 面板 / 时间序列 / 截面数据（基于规则，不依赖列名） |
| 变量角色选择 | 因变量、主解释变量、控制变量、实体 ID、时间列，含规则预填充 |
| 数据变换 | 对数变换、缩尾处理、标准化、均值/中位数填补、去重/去缺失行 |
| OLS 回归 | 普通最小二乘 + HC1 异方差稳健标准误（`statsmodels`） |
| 面板回归 | 混合 OLS、实体固定效应、随机效应、双向固定效应（`linearmodels`） |
| 聚类标准误 | 按实体聚类 |
| 计量诊断 | VIF、BP 检验、JB 检验、DW 统计量、Hausman 检验 |
| 模型推荐 | 基于规则的推荐（无大模型参与） |
| **多模型比较** | 对同一变量运行最多 6 个模型，并排展示拟合指标和诊断结果 |
| **透明推荐打分** | 多标准加权打分（结构、Hausman 检验、异方差处理、简约性、拟合优度） |
| **系数稳定性视图** | 对比主解释变量在不同模型设定下的系数表现 |
| **研究报告生成** | 确定性叙述章节，无大语言模型参与，不虚构任何统计数值 |
| **报告导出** | Markdown、HTML 和 JSON 归档，含可复现元数据 |
| 结果仪表板 | 系数表、系数图（95% CI）、残差图、相关矩阵热图 |
| 可复现导出 | 完整 JSON 归档，含软件版本信息 |

---

## 架构概览

```
上传 → 剖析 → 变量配置 → 数据变换 → 模型执行 → 结果展示
```

```
frontend/         Next.js 16 + TypeScript + Tailwind + Recharts
backend/          FastAPI + Pydantic v2 + pandas + statsmodels + linearmodels
sample_data/      世界银行风格合成面板数据（20 个国家 × 15 年）
docs/             架构文档、API 参考、计量规则、开发计划
```

**关注点分离：**
- `app/services/` — 纯数据函数（剖析、结构检测、变换）
- `app/analysis/` — 统计计算封装（OLS、面板、诊断）
- `app/api/` — 薄层 HTTP 路由，不含业务逻辑
- `app/schemas/` — 各层共享的 Pydantic 模型

---

## 技术栈

**后端**
- Python 3.12+
- FastAPI、Pydantic v2、pydantic-settings
- pandas、numpy、scipy
- statsmodels（OLS、诊断）
- linearmodels（面板回归）
- openpyxl（Excel 支持）
- pytest、httpx

**前端**
- Next.js 16、React 19、TypeScript 5
- Tailwind CSS v4
- Recharts v3
- lucide-react

---

## 目录结构

```
ai-econometrics-copilot/
├── backend/
│   ├── app/
│   │   ├── analysis/          # diagnostics.py, model_runner.py, ols_models.py, panel_models.py, model_recommender.py
│   │   ├── api/               # datasets.py, analyses.py
│   │   ├── core/              # config.py, errors.py, logging.py
│   │   ├── models/            # dataset_registry.py, analysis_registry.py
│   │   ├── schemas/           # dataset.py, modeling.py
│   │   └── services/          # transformation_service.py, data_profiler.py 等
│   └── tests/
├── frontend/
│   ├── app/
│   │   ├── page.tsx                         # 首页：上传 + 剖析仪表板
│   │   ├── datasets/[datasetId]/model/      # 变量配置 + 模型设置
│   │   └── analyses/[analysisId]/           # 结果仪表板
│   ├── components/
│   │   ├── modeling/                        # 变量选择、变换面板、模型配置
│   │   ├── results/                         # 系数表、系数图、残差图、热图、诊断卡片
│   │   └── ui/                              # 基础 UI 组件
│   ├── lib/                                 # api.ts, utils.ts
│   └── types/                               # dataset.ts, modeling.ts
├── sample_data/
│   └── world_bank_panel_sample.xlsx
└── docs/
```

---

## 环境要求

- Python 3.12+
- Node.js 20+
- `uv`（推荐）或 `pip`

---

## 后端安装

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

或使用 `uv`：
```bash
cd backend
uv sync
```

---

## 前端安装

```bash
cd frontend
npm install
```

---

## 环境变量

**后端**（可选，以下为默认值）：
```
ECOPILOT_CORS_ORIGINS=["http://localhost:3000"]
ECOPILOT_MAX_UPLOAD_SIZE_BYTES=52428800
ECOPILOT_LOG_LEVEL=INFO
```

**前端**（可选）：
```
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api
```

---

## 本地运行

**启动后端：**
```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

**启动前端：**
```bash
cd frontend
npm run dev
```

浏览器访问 [http://localhost:3000](http://localhost:3000)。

---

## 运行测试

```bash
cd backend
python -m pytest -q
```

预期结果：**76 个测试全部通过**。

前端类型检查：
```bash
cd frontend
npx tsc --noEmit
npm run build
```

---

## 使用示例

1. 上传 `sample_data/world_bank_panel_sample.xlsx`
2. 查看数据剖析结果——系统检测为面板数据（20 个实体 × 15 个时期）
3. 点击 **Configure & Run Model →**
4. 变量角色自动预填：`gdp_per_capita` 为因变量，`internet_users` 为解释变量
5. 可选：对右偏变量添加对数变换
6. 选择**实体固定效应**（面板数据推荐）
7. 启用按实体聚类标准误
8. 点击 **Run Analysis →**
9. 查看系数表、显著性星号、Hausman 检验、VIF、残差图
10. 导出可复现 JSON 归档

---

## 支持的模型

| 模型 | 依赖库 | 适用场景 |
|---|---|---|
| OLS | statsmodels | 截面数据 / 基准回归 |
| 稳健 OLS（HC1） | statsmodels | 存在异方差 |
| 混合 OLS | linearmodels | 面板数据，忽略面板结构 |
| 实体固定效应 | linearmodels | 控制时不变的个体异质性 |
| 随机效应 | linearmodels | 个体效应与解释变量不相关 |
| 双向固定效应 | linearmodels | 同时控制实体效应和时间效应 |

---

## 支持的诊断检验

| 诊断 | 用途 |
|---|---|
| VIF | 多重共线性检查（阈值：5 / 10） |
| Breusch-Pagan 检验 | 异方差检验 |
| Jarque-Bera 检验 | 残差正态性检验 |
| Durbin-Watson 统计量 | 一阶自相关检验 |
| Hausman 检验 | 固定效应 vs 随机效应选择 |
| 相关矩阵 | Pearson 相关系数热图 |
| 描述性统计 | 各变量汇总统计 |

---

## 当前限制

- 数据存储在内存中（无数据库），服务重启后数据丢失
- 无身份验证或多用户隔离
- 不支持任意公式输入（变量通过 UI 选择）
- 暂不支持 LaTeX/PDF 报告导出
- Hausman 检验使用伪逆矩阵以提升数值稳定性，极端情况下可能报告不可用
- 双向固定效应自动删除被完全吸收的变量（linearmodels `drop_absorbed=True`）

---

## 可复现性设计

每次 `POST /api/analyses/run` 均保存完整的分析记录，包括：
- 原始数据集元数据
- 每一步数据变换（含变换前后行数）
- 精确模型公式
- 全部系数和诊断结果
- 统计软件库版本
- 时间戳

通过 `GET /api/analyses/{id}/export/json` 导出。

---

## 推荐打分标准

| 标准 | 权重 |
|---|---|
| 结构兼容性 | 25% |
| Hausman 检验引导 | 20% |
| 异方差稳健性 | 15% |
| 模型拟合优度 | 15% |
| 简约性 | 10% |
| 样本量充足性 | 10% |
| 估计成功率 | 5% |

---

## 功能路线图

| 阶段 | 内容 | 状态 |
|---|---|---|
| Phase 1 | 数据上传、剖析、结构检测 | ✅ 已完成 |
| Phase 2 | 变量配置、数据变换 | ✅ 已完成 |
| Phase 3 | 回归执行、计量诊断 | ✅ 已完成 |
| Phase 4 | 多模型比较、透明推荐打分、研究报告生成 | ✅ 已完成 |
| Phase 5 | 自然语言研究问题映射、AI 规划层 | 计划中 |
| Phase 6 | 自主发现引擎，含有界搜索与多重检验校正 | 未来 |

---

## 因果语言免责声明

> 本分析识别的是统计关联关系，除非满足额外的识别假设，否则不能确立因果效应。