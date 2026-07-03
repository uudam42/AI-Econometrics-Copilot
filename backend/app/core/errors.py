"""Domain exceptions and a unified error response format."""
from __future__ import annotations

from fastapi import Request
from fastapi.responses import JSONResponse


class AppError(Exception):
    """Base class for user-facing application errors.

    Raised instead of letting raw Python/statsmodels tracebacks reach the client.
    """

    status_code: int = 400
    error_code: str = "app_error"

    def __init__(self, message: str, *, details: dict | None = None) -> None:
        self.message = message
        self.details = details or {}
        super().__init__(message)


class ValidationAppError(AppError):
    status_code = 422
    error_code = "validation_error"


class UnsupportedFileTypeError(AppError):
    status_code = 415
    error_code = "unsupported_file_type"


class FileTooLargeError(AppError):
    status_code = 413
    error_code = "file_too_large"


class DatasetNotFoundError(AppError):
    status_code = 404
    error_code = "dataset_not_found"


class ModelNotFoundError(AppError):
    status_code = 404
    error_code = "model_not_found"


class ModelExecutionError(AppError):
    """Raised when a statistical model cannot be estimated for a user-comprehensible reason."""

    status_code = 422
    error_code = "model_execution_error"


class ProjectNotFoundError(AppError):
    status_code = 404
    error_code = "project_not_found"


class ProjectDeletionError(AppError):
    status_code = 409
    error_code = "project_has_artifacts"


class StorageError(AppError):
    status_code = 500
    error_code = "storage_error"


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.error_code,
                "message": exc.message,
                "details": exc.details,
            }
        },
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    from app.core.logging import get_logger

    get_logger(__name__).exception("Unhandled exception while processing %s", request.url)
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "internal_error",
                "message": "An unexpected server error occurred. Please try again or contact support.",
                "details": {},
            }
        },
    )
