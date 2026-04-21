"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.features.catalog.router import router as catalog_router
from app.features.ingest.router import router as ingest_router
from app.features.reports.router import router as reports_router
from app.core.config import settings

app = FastAPI(
    title="Integration",
    version="0.1.0",
    description="Integration service API",
)

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_origins=[],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ingest_router, prefix=settings.API_V1_PREFIX)
app.include_router(catalog_router, prefix=settings.API_V1_PREFIX)
app.include_router(reports_router, prefix=settings.API_V1_PREFIX)


@app.get("/")
async def root() -> dict[str, str]:
    return {
        "message": "Welcome to the Integration API",
        "version": "0.1.0",
        "docs": "/docs",
    }
