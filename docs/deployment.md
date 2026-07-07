# Deployment Guide

[中文版](deployment.zh-CN.md)

## Overview

AI Econometrics Copilot is designed for single-user, local deployment. This guide covers Docker deployment, reverse proxy configuration, and production considerations.

---

## Docker Deployment

### Basic

```bash
docker compose up --build -d
```

This starts:
- **Backend** on port 8000 (FastAPI + Uvicorn)
- **Frontend** on port 3000 (Next.js)
- Data persists in `ai_econometrics_data` named volume

### Custom Ports

Edit `docker-compose.yml`:
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

### Health Checks

Both services include Docker health checks:
- Backend: `python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"`
- Frontend: `node -e "require('http').get('http://localhost:3000', r => process.exit(r.statusCode === 200 ? 0 : 1))"`

The frontend waits for the backend to be healthy before starting.

### Volume Management

```bash
# View data volume
docker volume inspect ai_econometrics_data

# Backup
docker run --rm -v ai_econometrics_data:/data -v $(pwd):/backup alpine \
  tar czf /backup/econometrics_backup.tar.gz -C /data .

# Restore
docker run --rm -v ai_econometrics_data:/data -v $(pwd):/backup alpine \
  tar xzf /backup/econometrics_backup.tar.gz -C /data

# Reset
docker compose down -v
```

---

## Reverse Proxy (Nginx)

Example Nginx configuration for serving both services behind a single domain:

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

Update environment variables:
```bash
ECOPILOT_CORS_ORIGINS='["https://econometrics.example.com"]'
NEXT_PUBLIC_API_BASE_URL=https://econometrics.example.com/api
```

---

## Environment Variables

All backend variables use the `ECOPILOT_` prefix. See [`.env.example`](../.env.example) for the complete list.

Key production settings:

| Variable | Production Value | Purpose |
|---|---|---|
| `ECOPILOT_LOG_LEVEL` | `WARNING` | Reduce log verbosity |
| `ECOPILOT_CORS_ORIGINS` | `["https://your-domain.com"]` | Restrict CORS |
| `ECOPILOT_MAX_UPLOAD_SIZE_BYTES` | Adjust as needed | Upload limit |

---

## Data Persistence

### SQLite

The default database is SQLite, stored at `data/ai_econometrics.db`. This is suitable for single-user deployment. For multi-user scenarios (not currently supported), consider PostgreSQL.

### File Storage

- Uploaded datasets: `data/uploads/`
- Generated artifacts: `data/artifacts/`

Both directories are created automatically on startup.

### Backup Strategy

```bash
# Stop services
docker compose stop

# Backup the entire data directory
tar czf backup_$(date +%Y%m%d).tar.gz -C backend data/

# Restart
docker compose start
```

---

## Production Considerations

### What This Platform Is

- A single-user research tool
- Local-first, no cloud dependency
- Designed for academic and research use

### What This Platform Is Not

- Not a multi-user SaaS application
- No built-in authentication or authorization
- No cloud sync or collaboration features
- Not designed for high-concurrency workloads

### Security Notes

- No authentication is built in — do not expose to the public internet without a reverse proxy and authentication layer
- SQLite is not designed for concurrent writes — single-user only
- File uploads are validated by extension and size but not scanned for malware
- CORS is configurable — restrict to your domain in production

### Performance

- SQLite handles typical research datasets well (up to ~1M rows)
- DataFrames are cached in memory after first load
- The application restarts cleanly — cached data is reloaded from disk
- Memory usage scales with dataset size; 4 GB RAM recommended for typical workloads

---

## Updating

```bash
git pull
docker compose up --build -d
```

Data in the named volume persists across rebuilds.

---

## Windows Desktop Distribution

For standalone Windows deployment without Docker or any runtime dependencies:

### Building the Installer

Prerequisites (developer machine only):
- Rust (`rustup default stable`)
- Node.js 18+
- Python 3.10+

```powershell
.\desktop\scripts\build-desktop.ps1
```

Output: `desktop/src-tauri/target/release/bundle/msi/` and `nsis/`

### End User Installation

1. Download the installer (`.msi` or `Setup.exe`)
2. Run the installer
3. Open from the Start Menu

No Docker, Python, Node.js, or browser required.

### Desktop Data Location

User data is stored in `%LOCALAPPDATA%\AI Econometrics Copilot\`:
- `database/` — SQLite database (persists across upgrades)
- `uploads/`, `artifacts/`, `exports/` — user files
- `logs/` — application logs

Uninstalling does not delete user data.

### Known Limitations

- Windows only (macOS and Linux desktop packages not yet built)
- Unsigned build — Windows SmartScreen warnings expected
- No automatic updates
- No cloud sync
