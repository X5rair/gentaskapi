"""Router for ingest endpoints."""

from uuid import UUID

from fastapi import APIRouter, Request, status

from app.features.ingest.schemas import (
    IngestAcceptedResponse,
    IngestJobListResponse,
    IngestJobResponse,
)
from app.features.ingest.service import IngestService

router = APIRouter(prefix="/ingest", tags=["ingest"])


@router.post(
    "/process",
    response_model=IngestAcceptedResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def process_ingest(
    request: Request,
) -> IngestAcceptedResponse:
    job = await IngestService.create_job_from_request(request)
    return IngestAcceptedResponse(
        message="Payload accepted and queued for background processing.",
        job=IngestJobResponse.model_validate(job),
    )


@router.get("/jobs", response_model=IngestJobListResponse)
async def list_ingest_jobs(
    limit: int = 20,
) -> IngestJobListResponse:
    jobs = await IngestService.list_jobs(limit=min(limit, 50))
    return IngestJobListResponse(
        items=[IngestJobResponse.model_validate(job) for job in jobs]
    )


@router.get("/jobs/{job_id}", response_model=IngestJobResponse)
async def get_ingest_job(
    job_id: UUID,
) -> IngestJobResponse:
    job = await IngestService.get_job(job_id=job_id)
    return IngestJobResponse.model_validate(job)
