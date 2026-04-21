"""Schemas for ingest endpoints."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class IngestJobResponse(BaseModel):
    id: UUID
    source_system: str
    company_name: str | None = None
    note: str | None = None
    payload_kind: str
    status: str
    original_filename: str
    stored_path: str
    payload_size_bytes: int
    extracted_file_count: int
    sql_statement_count: int
    sql_file_names: list[str]
    preview_payload: list[dict]
    received_at: datetime
    processing_started_at: datetime | None = None
    processing_finished_at: datetime | None = None
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime


class IngestAcceptedResponse(BaseModel):
    message: str
    job: IngestJobResponse


class IngestJobListResponse(BaseModel):
    items: list[IngestJobResponse]
