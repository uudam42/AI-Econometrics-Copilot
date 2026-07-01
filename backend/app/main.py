"""FastAPI application entrypoint for AI Econometrics Copilot."""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import analyses, datasets
from app.core.config import settings
from app.core.errors import AppError, app_error_handler, unhandled_exception_handler
from app.core.logging import configure_logging

configure_logging()

app = FastAPI(
    title=settings.app_name,
    description="An explainable AI-assisted econometric modeling platform for economic research.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(AppError, app_error_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

app.include_router(datasets.router, prefix=settings.api_prefix)
app.include_router(analyses.router, prefix=settings.api_prefix)


@app.get("/health", tags=["meta"])
async def health() -> dict:
    return {"status": "ok", "app": settings.app_name}
