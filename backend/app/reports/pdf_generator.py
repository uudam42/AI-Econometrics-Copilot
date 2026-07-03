"""PDF export — documented placeholder.

WeasyPrint requires native Pango/Cairo libraries (libpango-1.0-0, libcairo2)
that are not reliably available across all deployment environments. This module
raises a clear error rather than failing silently.

To enable PDF export:
  1. Install system packages: libpango-1.0-0, libcairo2, libgdk-pixbuf2.0-0
  2. pip install weasyprint>=60
  3. Remove the raise in generate_pdf() below
"""
from __future__ import annotations

from app.core.errors import AppError


class PDFExportUnavailableError(AppError):
    status_code = 501
    error_code = "pdf_export_unavailable"


def generate_pdf(html_content: str, output_path: str) -> None:
    raise PDFExportUnavailableError(
        "PDF export is not available in this environment. "
        "It requires native Pango/Cairo libraries (libpango-1.0-0, libcairo2) "
        "which are not installed. Use DOCX or LaTeX export instead."
    )
