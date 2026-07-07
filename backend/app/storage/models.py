"""SQLAlchemy table models for persistent storage."""
from __future__ import annotations

from sqlalchemy import Column, DateTime, Float, Integer, String, Text
from sqlalchemy.types import JSON

from app.storage.database import Base


class ProjectRow(Base):
    __tablename__ = "projects"

    id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    description = Column(Text, default="")
    research_question = Column(Text, default="")
    status = Column(String, default="draft")
    tags = Column(JSON, default=list)
    default_dataset_id = Column(String, nullable=True)
    research_context = Column(Text, default="")
    notes = Column(Text, default="")
    methodology_notes = Column(Text, default="")
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)


class DatasetRow(Base):
    __tablename__ = "datasets"

    id = Column(String, primary_key=True)
    project_id = Column(String, nullable=True)
    filename = Column(String, nullable=False)
    storage_path = Column(String, nullable=False)
    file_type = Column(String, nullable=True)
    checksum = Column(String, nullable=True)
    n_rows = Column(Integer, nullable=True)
    n_columns = Column(Integer, nullable=True)
    uploaded_at = Column(DateTime, nullable=False)
    profile_json = Column(JSON, nullable=True)
    structure_json = Column(JSON, nullable=True)


class AnalysisRow(Base):
    __tablename__ = "analyses"

    id = Column(String, primary_key=True)
    project_id = Column(String, nullable=True)
    dataset_id = Column(String, nullable=False)
    dataset_filename = Column(String, nullable=True)
    created_at = Column(DateTime, nullable=False)
    config_json = Column(JSON, nullable=True)
    result_json = Column(JSON, nullable=True)
    diagnostics_json = Column(JSON, nullable=True)
    transformation_log_json = Column(JSON, nullable=True)


class ComparisonRow(Base):
    __tablename__ = "comparisons"

    id = Column(String, primary_key=True)
    project_id = Column(String, nullable=True)
    dataset_id = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False)
    request_json = Column(JSON, nullable=True)
    result_json = Column(JSON, nullable=True)


class PlanRow(Base):
    __tablename__ = "plans"

    id = Column(String, primary_key=True)
    project_id = Column(String, nullable=True)
    dataset_id = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False)
    plan_json = Column(JSON, nullable=True)
    approved = Column(Integer, default=0)


class ReportRow(Base):
    __tablename__ = "reports"

    id = Column(String, primary_key=True)
    project_id = Column(String, nullable=True)
    source_type = Column(String, nullable=True)
    source_id = Column(String, nullable=True)
    created_at = Column(DateTime, nullable=False)
    artifact_json = Column(JSON, nullable=True)


class DiscoveryRow(Base):
    __tablename__ = "discoveries"

    id = Column(String, primary_key=True)
    project_id = Column(String, nullable=True)
    dataset_id = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False)
    result_json = Column(JSON, nullable=True)


class PublicationExportRow(Base):
    __tablename__ = "publication_exports"

    id = Column(String, primary_key=True)
    project_id = Column(String, nullable=True)
    source_type = Column(String, nullable=False)
    source_id = Column(String, nullable=False)
    title = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False)
    config_json = Column(JSON, nullable=True)
    result_json = Column(JSON, nullable=True)


class QuickAnalyzeSessionRow(Base):
    __tablename__ = "quick_analyze_sessions"

    id = Column(String, primary_key=True)
    stage = Column(String, nullable=False, default="created")
    project_id = Column(String, nullable=True)
    dataset_id = Column(String, nullable=True)
    plan_id = Column(String, nullable=True)
    analysis_id = Column(String, nullable=True)
    research_question = Column(Text, nullable=True)
    analysis_intent = Column(String, default="association")
    recommendation_json = Column(JSON, nullable=True)
    summary_json = Column(JSON, nullable=True)
    progress_message = Column(Text, default="")
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)


class TimelineEventRow(Base):
    __tablename__ = "timeline_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(String, nullable=False)
    event_type = Column(String, nullable=False)
    artifact_type = Column(String, nullable=True)
    artifact_id = Column(String, nullable=True)
    description = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False)
