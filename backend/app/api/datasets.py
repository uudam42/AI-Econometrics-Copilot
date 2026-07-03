"""Dataset upload, overview, profiling, and transformation endpoints."""
from __future__ import annotations

from fastapi import APIRouter, File, UploadFile

from app.storage.repositories import dataset_repository
from app.schemas.dataset import (
    DatasetOverviewResponse,
    DatasetProfileResponse,
    DatasetSummary,
)
from app.schemas.modeling import AnalysisConfigurationRequest, TransformResult
from app.services.column_typing import infer_all_column_types
from app.services.data_profiler import profile_dataset
from app.services.dataset_service import build_preview, ingest_upload
from app.services.structure_detector import detect_structure

router = APIRouter(prefix="/datasets", tags=["datasets"])


def _build_overview(record) -> DatasetOverviewResponse:
    df = record.dataframe
    return DatasetOverviewResponse(
        dataset_id=record.dataset_id,
        filename=record.filename,
        n_rows=df.shape[0],
        n_columns=df.shape[1],
        column_types=infer_all_column_types(df),
        preview_rows=build_preview(df),
        uploaded_at=record.uploaded_at,
    )


@router.post("/upload", response_model=DatasetOverviewResponse)
async def upload_dataset(file: UploadFile = File(...)) -> DatasetOverviewResponse:
    content = await file.read()
    record = ingest_upload(filename=file.filename or "", content=content)
    return _build_overview(record)


@router.get("/{dataset_id}", response_model=DatasetSummary)
async def get_dataset(dataset_id: str) -> DatasetSummary:
    record = dataset_repository.get(dataset_id)
    df = record.dataframe
    return DatasetSummary(
        dataset_id=record.dataset_id,
        filename=record.filename,
        n_rows=df.shape[0],
        n_columns=df.shape[1],
        columns=list(df.columns),
        uploaded_at=record.uploaded_at,
    )


@router.get("/{dataset_id}/overview", response_model=DatasetOverviewResponse)
async def get_dataset_overview(dataset_id: str) -> DatasetOverviewResponse:
    record = dataset_repository.get(dataset_id)
    return _build_overview(record)


@router.get("/{dataset_id}/profile", response_model=DatasetProfileResponse)
async def get_dataset_profile(dataset_id: str) -> DatasetProfileResponse:
    record = dataset_repository.get(dataset_id)
    df = record.dataframe
    quality = profile_dataset(dataset_id, df)
    structure = detect_structure(df)
    return DatasetProfileResponse(dataset_id=dataset_id, quality=quality, structure=structure)


@router.post("/{dataset_id}/transform", response_model=TransformResult)
async def transform_dataset(dataset_id: str, config: AnalysisConfigurationRequest) -> TransformResult:
    """Apply transformations to a copy of the dataset and persist the processed copy."""
    record = dataset_repository.get(dataset_id)
    ops = [t.model_dump() for t in config.transformations]
    rows_before = len(record.dataframe)
    from app.services.transformation_service import apply_transformations
    processed_df, log = apply_transformations(record.dataframe, ops)
    record.processed_dataframe = processed_df
    record.transformation_log = [entry.model_dump() for entry in log]
    new_cols = [c for c in processed_df.columns if c not in record.dataframe.columns]
    return TransformResult(
        dataset_id=dataset_id,
        rows_before=rows_before,
        rows_after=len(processed_df),
        columns_added=new_cols,
        log=log,
    )
