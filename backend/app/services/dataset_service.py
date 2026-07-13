"""File ingestion: validation, parsing, and dataset registration."""
from __future__ import annotations

import uuid
from pathlib import Path

import pandas as pd

import app.core.config as _config
from app.core.errors import UnsupportedFileTypeError, ValidationAppError, FileTooLargeError
from app.core.logging import get_logger
from app.storage.repositories import DatasetRecord, dataset_repository

logger = get_logger(__name__)


def _validate_extension(filename: str) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix not in _config.settings.allowed_extensions:
        raise UnsupportedFileTypeError(
            f"File type '{suffix}' is not supported. Allowed types: "
            f"{', '.join(_config.settings.allowed_extensions)}.",
            details={"filename": filename},
        )
    return suffix


def _parse_dataframe(path: Path, suffix: str) -> pd.DataFrame:
    try:
        if suffix == ".csv":
            df = pd.read_csv(path)
        else:
            df = pd.read_excel(path)
    except Exception as exc:  # pragma: no cover - defensive, re-raised as AppError below
        raise ValidationAppError(
            "The file could not be parsed. Please check that it is a valid, "
            "non-corrupted CSV or Excel file.",
            details={"parser_error": str(exc)},
        ) from exc

    if df.shape[1] == 0:
        raise ValidationAppError("The uploaded file contains no columns.")
    if df.shape[0] == 0:
        raise ValidationAppError("The uploaded file contains no data rows.")

    return df


def ingest_upload(
    filename: str,
    content: bytes,
    project_id: str | None = None,
) -> DatasetRecord:
    """Validate, persist, and register an uploaded CSV/Excel file."""
    if not filename:
        raise ValidationAppError("Uploaded file is missing a filename.")

    suffix = _validate_extension(filename)

    if len(content) > _config.settings.max_upload_size_bytes:
        raise FileTooLargeError(
            f"File exceeds the maximum allowed size of "
            f"{_config.settings.max_upload_size_bytes // (1024 * 1024)} MB.",
            details={"size_bytes": len(content)},
        )
    if len(content) == 0:
        raise ValidationAppError("Uploaded file is empty.")

    stored_name = f"{uuid.uuid4()}{suffix}"
    stored_path = _config.settings.upload_dir / stored_name
    stored_path.write_bytes(content)

    df = _parse_dataframe(stored_path, suffix)

    record = dataset_repository.create(
        filename=filename,
        original_path=stored_path,
        dataframe=df,
        project_id=project_id,
    )
    logger.info(
        "Ingested dataset %s (%s): %d rows x %d columns",
        record.dataset_id,
        filename,
        df.shape[0],
        df.shape[1],
    )
    return record


def build_preview(df: pd.DataFrame, n_rows: int | None = None) -> list[dict]:
    n = n_rows or _config.settings.preview_row_count
    preview_df = df.head(n)
    return preview_df.astype(object).where(preview_df.notna(), None).to_dict(orient="records")
