"""Router for the integration catalog admin API."""

from fastapi import APIRouter

from app.features.catalog.schemas import CatalogState
from app.features.catalog.service import CatalogService

router = APIRouter(prefix="/catalog", tags=["catalog"])


@router.get("", response_model=CatalogState)
async def get_catalog() -> CatalogState:
    return await CatalogService.load_catalog()


@router.put("", response_model=CatalogState)
async def put_catalog(state: CatalogState) -> CatalogState:
    return await CatalogService.save_catalog(state)

