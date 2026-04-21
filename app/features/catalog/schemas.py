"""Schemas for the integration catalog admin API."""

from datetime import datetime

from pydantic import BaseModel, Field


class CatalogMeta(BaseModel):
    schema_version: int = 1
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class CatalogCountry(BaseModel):
    id: str
    name: str
    code: str | None = None
    sort_order: int = 0


class CatalogConfiguration(BaseModel):
    id: str
    country_id: str
    name: str
    version_code: str | None = None
    extension_version: str | None = None
    sort_order: int = 0


class CatalogVersion(BaseModel):
    id: str
    configuration_id: str
    version: str
    release: str | None = None
    sort_order: int = 0


class CatalogClient(BaseModel):
    id: str
    name: str
    bin: str | None = None
    active: bool = True
    sort_order: int = 0


class CatalogReportColumn(BaseModel):
    id: str
    report_name: str
    report_prefix: str = "Отчет_"
    eng_name: str
    rus_name: str
    column_number: int
    visible: bool = True
    grouped: bool = False
    column_type: str = "Строка"


class CatalogQuery(BaseModel):
    id: str
    parent_id: str | None = None
    code: str
    name: str
    query_type: str = "general"
    hide_from_client: bool = False
    client_id: str | None = None
    country_id: str | None = None
    configuration_ids: list[str] = Field(default_factory=list)
    version_ids: list[str] = Field(default_factory=list)
    query_text: str = ""
    parameters_text: str = ""
    sort_order: int = 0
    columns: list[CatalogReportColumn] = Field(default_factory=list)


class CatalogState(BaseModel):
    meta: CatalogMeta = Field(default_factory=CatalogMeta)
    countries: list[CatalogCountry] = Field(default_factory=list)
    configurations: list[CatalogConfiguration] = Field(default_factory=list)
    versions: list[CatalogVersion] = Field(default_factory=list)
    clients: list[CatalogClient] = Field(default_factory=list)
    queries: list[CatalogQuery] = Field(default_factory=list)
