"""Application configuration via environment variables."""
from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="ECOPILOT_", env_file=".env", extra="ignore")

    app_name: str = "AI Econometrics Copilot"
    api_prefix: str = "/api"
    cors_origins: list[str] = ["http://localhost:3000"]

    database_url: str = "sqlite:///./data/ai_econometrics.db"
    data_dir: Path = Path("data")
    upload_dir: Path = Path("data/uploads")
    artifact_dir: Path = Path("data/artifacts")
    max_upload_size_bytes: int = 50 * 1024 * 1024  # 50 MB
    allowed_extensions: tuple[str, ...] = (".csv", ".xlsx", ".xls")

    preview_row_count: int = 10
    outlier_iqr_multiplier: float = 1.5
    outlier_zscore_threshold: float = 3.0
    high_skew_threshold: float = 1.0
    vif_warning_threshold: float = 5.0
    vif_severe_threshold: float = 10.0
    heteroskedasticity_alpha: float = 0.05

    log_level: str = "INFO"


settings = Settings()
settings.upload_dir.mkdir(parents=True, exist_ok=True)
