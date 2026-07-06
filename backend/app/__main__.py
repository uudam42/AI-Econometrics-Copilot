"""Entry point for standalone/sidecar execution: python -m app"""
import os

import uvicorn

if __name__ == "__main__":
    port = int(os.environ.get("AI_ECONOMETRICS_PORT", "8000"))
    host = os.environ.get("AI_ECONOMETRICS_HOST", "127.0.0.1")

    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        log_level=os.environ.get("ECOPILOT_LOG_LEVEL", "info").lower(),
    )
