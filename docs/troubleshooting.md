# Troubleshooting

[中文版](troubleshooting.zh-CN.md)

## Startup Issues

### Port already in use

```
Error: Port 8000 is already in use
```

**Solution:**
```bash
# Find and kill the process
lsof -ti :8000 | xargs kill   # macOS/Linux
# Or use the stop script
bash scripts/stop-local.sh
```

### Python version too old

```
ERROR: Python 3.10+ is required
```

**Solution:** Install Python 3.10 or later from [python.org](https://www.python.org/downloads/).

### Node.js version too old

```
ERROR: Node.js 18+ is required
```

**Solution:** Install Node.js 18+ from [nodejs.org](https://nodejs.org/).

### Virtual environment activation fails

```
source: command not found
```

**Solution:** You're using a non-bash shell. Use the appropriate activation:
```bash
source .venv/bin/activate      # bash/zsh
.venv/Scripts/activate         # Windows cmd
.venv/Scripts/Activate.ps1     # Windows PowerShell
```

### pip install fails with compilation errors

**Solution:** Install build tools:
```bash
# macOS
xcode-select --install

# Ubuntu/Debian
sudo apt-get install build-essential python3-dev

# Windows
# Install Visual C++ Build Tools
```

---

## Docker Issues

### Docker Compose not found

```
docker: 'compose' is not a docker command
```

**Solution:** Install Docker Compose v2:
```bash
# On recent Docker Desktop, compose is built-in
docker compose version

# If using older Docker, install the plugin
# See: https://docs.docker.com/compose/install/
```

### Build fails with memory error

**Solution:** Increase Docker memory allocation in Docker Desktop settings (recommended: 4 GB+).

### Container health check fails

```
backend  | unhealthy
```

**Solution:** Check backend logs:
```bash
docker compose logs backend
```

Common causes:
- Missing dependencies in requirements.txt
- Database initialization error
- Port conflict inside the container

---

## Runtime Issues

### CORS error in browser console

```
Access to fetch has been blocked by CORS policy
```

**Solution:** Set the CORS origin to match your frontend URL:
```bash
export ECOPILOT_CORS_ORIGINS='["http://localhost:3000"]'
```

### Upload fails with "File too large"

**Solution:** Increase the upload limit:
```bash
export ECOPILOT_MAX_UPLOAD_SIZE_BYTES=104857600  # 100 MB
```

### Dataset profile shows "structure unknown"

This happens when the data doesn't have clear panel, time-series, or cross-sectional patterns.

**Solution:** The system still works — it defaults to OLS. You can manually assign variable roles.

### Hausman test unavailable

The Hausman test requires both Fixed Effects and Random Effects to converge. Near-singular covariance matrices can prevent computation.

**Solution:** This is expected for small samples or highly collinear data. The system reports "unavailable" transparently. Choose between FE and RE based on economic theory.

### Two-way FE absorbs primary variable

When the primary IV is collinear with entity or time dummies, Two-Way FE absorbs it.

**Solution:** The system warns about this. Consider using one-way FE instead, or rethink the variable specification.

### PDF export returns 501

PDF export is a documented placeholder. It requires native Pango/Cairo libraries.

**Solution:** Use DOCX or LaTeX export instead. Both are fully functional.

---

## Data Issues

### Excel file won't upload

**Solution:** Ensure the file has a `.xlsx` or `.xls` extension. The system uses `openpyxl` for `.xlsx` and `xlrd` for `.xls`.

### Missing values not detected

**Solution:** Check that missing values are encoded as empty cells, `NA`, `NaN`, or `None`. Custom encodings (e.g., `-999`, `N/A`) are not auto-detected.

### Wrong column types detected

The type inference is rule-based. It can misclassify columns.

**Solution:** You can override variable roles in the model configuration step. Type detection does not prevent any analysis.

---

## Frontend Issues

### Page shows blank/loading forever

**Solution:**
1. Check that the backend is running (`curl http://localhost:8000/health`)
2. Check browser console for errors (F12 → Console)
3. Verify `NEXT_PUBLIC_API_BASE_URL` points to the backend

### TypeScript errors during build

**Solution:**
```bash
cd frontend
npx tsc --noEmit  # shows all type errors
```

Most type errors are in the source, not configuration. Check the error messages for file paths and line numbers.

---

## Desktop Application Issues

### SmartScreen warning on Windows

Unsigned builds trigger Windows SmartScreen. Click "More info" → "Run anyway".

### Desktop app shows blank window

The backend sidecar may have failed to start.

**Solution:**
1. Click **Help → View Logs** in the app menu
2. Check `backend.log` for startup errors
3. Ensure no other process is using the selected port

### Desktop app data location

All data is in `%LOCALAPPDATA%\AI Econometrics Copilot\`:
- `database/` — SQLite database
- `uploads/` — uploaded datasets
- `artifacts/` — analysis artifacts
- `exports/` — generated documents
- `logs/` — application logs

### Uninstall preserves data

Uninstalling the app does not delete user data. To remove all data, manually delete `%LOCALAPPDATA%\AI Econometrics Copilot\`.

---

## Getting Help

- Check the [API documentation](http://localhost:8000/docs) (Swagger UI)
- Review the [architecture documentation](architecture.md)
- File an issue on the project repository
