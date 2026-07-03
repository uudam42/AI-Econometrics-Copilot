# Quick Start Guide

[中文版](quickstart.zh-CN.md)

## Option 1: Docker (Recommended)

```bash
git clone https://github.com/your-org/ai-econometrics-copilot.git
cd ai-econometrics-copilot
docker compose up --build
```

Open [http://localhost:3000](http://localhost:3000). Done.

## Option 2: Local Development

### Prerequisites

- Python 3.10+ (`python --version`)
- Node.js 18+ (`node --version`)

### Automated

```bash
bash scripts/start-local.sh
```

The script checks dependencies, creates a virtual environment, installs packages, starts both services, and opens the browser.

### Manual

**Backend:**
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

## First Steps

1. Open [http://localhost:3000](http://localhost:3000)
2. Click **Try Sample Dataset** to create a demo project with pre-loaded World Bank panel data
3. The dataset is profiled automatically — review the panel structure (20 countries, 15 years)
4. Click **Configure & Run Model** to set up your first regression
5. Variable roles are pre-filled; select Fixed Effects and click **Run Analysis**
6. View the coefficient table, diagnostics, and residual plots
7. Try **Compare Models** to run multiple specifications side-by-side

## Stopping the Application

```bash
bash scripts/stop-local.sh       # macOS / Linux
powershell scripts/stop-local.ps1  # Windows
```

Or with Docker:
```bash
docker compose down
```

## Resetting Data

```bash
bash scripts/reset-local-data.sh       # local
docker compose down -v                 # Docker
```

## Next Steps

- [User Guide](user-guide.md) — full feature walkthrough
- [Troubleshooting](troubleshooting.md) — common issues and solutions
- [Deployment](deployment.md) — production deployment guidance
