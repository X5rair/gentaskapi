"""Schemas for reports service endpoints."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class ReportSettings(BaseModel):
    report_order: list[str] = Field(default_factory=list)
    visible_columns: list[str] = Field(default_factory=list)
    column_order: list[str] = Field(default_factory=list)
    grouped_columns: list[str] = Field(default_factory=list)
    period_mode: str = "monthly"


class ComparisonSettings(BaseModel):
    mapping_columns: dict[str, str] = Field(default_factory=dict)
    template_name: str = "default"
    compare_database_ids: list[str] = Field(default_factory=list)
    period_modes: list[str] = Field(default_factory=lambda: ["week", "month", "quarter", "year"])
    visible_columns: list[str] = Field(default_factory=list)
    column_order: list[str] = Field(default_factory=list)
    grouped_columns: list[str] = Field(default_factory=list)


class ChartSettings(BaseModel):
    report_chart_types: dict[str, str] = Field(default_factory=dict)
    compare_chart_type: str = "bar"


class OrganizationSettings(BaseModel):
    reports: ReportSettings = Field(default_factory=ReportSettings)
    comparison: ComparisonSettings = Field(default_factory=ComparisonSettings)
    charts: ChartSettings = Field(default_factory=ChartSettings)


class OrganizationCreateRequest(BaseModel):
    name: str
    bin: str = Field(min_length=12, max_length=12)


class OrganizationResponse(BaseModel):
    id: str
    name: str
    bin: str
    created_at: datetime
    updated_at: datetime
    settings: OrganizationSettings


class OneCDatabaseCreateRequest(BaseModel):
    organization_id: str
    one_c_database_name: str
    customer_display_name: str
    configuration: str
    release: str


class OneCDatabaseResponse(BaseModel):
    id: str
    organization_id: str
    one_c_database_name: str
    customer_display_name: str
    configuration: str
    release: str
    mysql_database_name: str
    api_key: str
    active: bool
    last_sync_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class AuthKeyResponse(BaseModel):
    database_id: str
    api_key: str
    mysql_database_name: str
    updated_at: datetime


class InviteRequest(BaseModel):
    organization_id: str
    email: str
    can_view_reports: bool = True
    can_view_charts: bool = True
    can_view_comparisons: bool = True
    can_view_settlements: bool = False
    can_view_db_and_keys: bool = False


class InviteResponse(BaseModel):
    id: str
    organization_id: str
    email: str
    status: str
    can_view_reports: bool
    can_view_charts: bool
    can_view_comparisons: bool
    can_view_settlements: bool
    can_view_db_and_keys: bool
    created_at: datetime


class SettlementEntryCreateRequest(BaseModel):
    organization_id: str
    document_type: str
    document_number: str
    amount: float
    due_date: datetime
    paid: bool = False
    document_url: str | None = None


class SettlementEntryResponse(BaseModel):
    id: str
    organization_id: str
    document_type: str
    document_number: str
    amount: float
    due_date: datetime
    paid: bool
    document_url: str | None = None
    created_at: datetime


class ReportAccessStatusResponse(BaseModel):
    organization_id: str
    reports_blocked: bool
    unpaid_documents: int


class Md5RecordIn(BaseModel):
    md5: str | None = None
    payload: dict = Field(default_factory=dict)


class Md5UpsertRequest(BaseModel):
    database_id: str
    table_name: str
    records: list[Md5RecordIn]


class Md5UpsertResponse(BaseModel):
    database_id: str
    table_name: str
    inserted: int
    skipped_existing: int
    total_after: int


class Md5HashListResponse(BaseModel):
    database_id: str
    table_name: str
    hashes: list[str]


class Md5DeleteRequest(BaseModel):
    database_id: str
    table_name: str
    hashes: list[str]


class Md5DeleteResponse(BaseModel):
    database_id: str
    table_name: str
    deleted: int
    total_after: int

