"""Router for reports and integration APIs from technical specification."""

from __future__ import annotations

from fastapi import APIRouter, status

from app.features.reports.schemas import (
    AuthKeyResponse,
    InviteRequest,
    InviteResponse,
    Md5DeleteRequest,
    Md5DeleteResponse,
    Md5HashListResponse,
    Md5UpsertRequest,
    Md5UpsertResponse,
    OneCDatabaseCreateRequest,
    OneCDatabaseResponse,
    OrganizationCreateRequest,
    OrganizationResponse,
    OrganizationSettings,
    ReportAccessStatusResponse,
    SettlementEntryCreateRequest,
    SettlementEntryResponse,
)
from app.features.reports.service import ReportsService

router = APIRouter(prefix="/reports", tags=["reports"])


@router.post(
    "/organizations",
    response_model=OrganizationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_organization(payload: OrganizationCreateRequest) -> OrganizationResponse:
    created = await ReportsService.create_organization(
        name=payload.name,
        bin_value=payload.bin,
    )
    return OrganizationResponse.model_validate(created)


@router.get("/organizations", response_model=list[OrganizationResponse])
async def list_organizations() -> list[OrganizationResponse]:
    organizations = await ReportsService.list_organizations()
    return [OrganizationResponse.model_validate(item) for item in organizations]


@router.get(
    "/organizations/{organization_id}/settings",
    response_model=OrganizationSettings,
)
async def get_organization_settings(organization_id: str) -> OrganizationSettings:
    settings = await ReportsService.get_organization_settings(organization_id)
    return OrganizationSettings.model_validate(settings)


@router.put(
    "/organizations/{organization_id}/settings",
    response_model=OrganizationSettings,
)
async def update_organization_settings(
    organization_id: str,
    payload: OrganizationSettings,
) -> OrganizationSettings:
    saved = await ReportsService.update_organization_settings(organization_id, payload)
    return OrganizationSettings.model_validate(saved)


@router.post(
    "/databases",
    response_model=OneCDatabaseResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_database(payload: OneCDatabaseCreateRequest) -> OneCDatabaseResponse:
    created = await ReportsService.create_database(payload.model_dump(mode="json"))
    return OneCDatabaseResponse.model_validate(created)


@router.get("/databases", response_model=list[OneCDatabaseResponse])
async def list_databases(organization_id: str | None = None) -> list[OneCDatabaseResponse]:
    items = await ReportsService.list_databases(organization_id=organization_id)
    return [OneCDatabaseResponse.model_validate(item) for item in items]


@router.delete(
    "/databases/{database_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_database(database_id: str) -> None:
    await ReportsService.delete_database(database_id)


@router.get("/databases/{database_id}/auth-keys", response_model=AuthKeyResponse)
async def get_auth_keys(database_id: str) -> AuthKeyResponse:
    data = await ReportsService.get_auth_keys(database_id)
    return AuthKeyResponse.model_validate(data)


@router.post(
    "/invitations",
    response_model=InviteResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_invitation(payload: InviteRequest) -> InviteResponse:
    created = await ReportsService.create_invite(payload.model_dump(mode="json"))
    return InviteResponse.model_validate(created)


@router.get("/invitations", response_model=list[InviteResponse])
async def list_invitations(organization_id: str | None = None) -> list[InviteResponse]:
    invites = await ReportsService.list_invites(organization_id=organization_id)
    return [InviteResponse.model_validate(item) for item in invites]


@router.post(
    "/settlements",
    response_model=SettlementEntryResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_settlement(payload: SettlementEntryCreateRequest) -> SettlementEntryResponse:
    created = await ReportsService.create_settlement(payload.model_dump(mode="json"))
    return SettlementEntryResponse.model_validate(created)


@router.get(
    "/settlements/{organization_id}",
    response_model=list[SettlementEntryResponse],
)
async def list_settlements(organization_id: str) -> list[SettlementEntryResponse]:
    items = await ReportsService.list_settlements(organization_id=organization_id)
    return [SettlementEntryResponse.model_validate(item) for item in items]


@router.get(
    "/access-status/{organization_id}",
    response_model=ReportAccessStatusResponse,
)
async def get_access_status(organization_id: str) -> ReportAccessStatusResponse:
    status_payload = await ReportsService.get_report_access_status(organization_id=organization_id)
    return ReportAccessStatusResponse.model_validate(status_payload)


@router.post(
    "/md5/upsert",
    response_model=Md5UpsertResponse,
)
async def md5_upsert(payload: Md5UpsertRequest) -> Md5UpsertResponse:
    result = await ReportsService.md5_upsert(
        database_id=payload.database_id,
        table_name=payload.table_name,
        records=[item.model_dump(mode="json") for item in payload.records],
    )
    return Md5UpsertResponse.model_validate(result)


@router.get(
    "/md5/hash-list",
    response_model=Md5HashListResponse,
)
async def md5_hash_list(database_id: str, table_name: str) -> Md5HashListResponse:
    result = await ReportsService.md5_hash_list(database_id=database_id, table_name=table_name)
    return Md5HashListResponse.model_validate(result)


@router.post(
    "/md5/delete",
    response_model=Md5DeleteResponse,
)
async def md5_delete(payload: Md5DeleteRequest) -> Md5DeleteResponse:
    result = await ReportsService.md5_delete(
        database_id=payload.database_id,
        table_name=payload.table_name,
        hashes=payload.hashes,
    )
    return Md5DeleteResponse.model_validate(result)

