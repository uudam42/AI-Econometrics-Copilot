"""FastAPI application entrypoint for AI Econometrics Copilot."""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import analyses, comparisons, datasets, discovery, onboarding, planning, projects, publication_exports, reports
from app.core.config import settings
from app.core.errors import AppError, app_error_handler, unhandled_exception_handler
from app.core.logging import configure_logging, get_logger

configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.storage.database import init_db
    init_db()
    logger.info("Persistence layer initialized — SQLite + file storage ready")
    yield


app = FastAPI(
    title=settings.app_name,
    description="An explainable AI-assisted econometric modeling platform for economic research.",
    version="0.2.0",
    lifespan=lifespan,
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

app.include_router(projects.router, prefix=settings.api_prefix)
app.include_router(datasets.router, prefix=settings.api_prefix)
app.include_router(analyses.router, prefix=settings.api_prefix)
app.include_router(comparisons.router, prefix=settings.api_prefix)
app.include_router(reports.router, prefix=settings.api_prefix)
app.include_router(planning.router, prefix=settings.api_prefix)
app.include_router(discovery.router, prefix=settings.api_prefix)
app.include_router(publication_exports.router, prefix=settings.api_prefix)
app.include_router(onboarding.router, prefix=settings.api_prefix)


@app.get("/health", tags=["meta"])
async def health() -> dict:
    return {"status": "ok", "app": settings.app_name, "version": "0.2.0"}
