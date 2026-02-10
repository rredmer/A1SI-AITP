from fastapi import APIRouter, HTTPException

from app.deps import JobServiceDep
from app.schemas.job import JobRead

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("/", response_model=list[JobRead])
async def list_jobs(
    service: JobServiceDep,
    job_type: str | None = None,
    limit: int = 50,
) -> list:
    return await service.list_jobs(job_type=job_type, limit=limit)


@router.get("/{job_id}")
async def get_job(job_id: str, service: JobServiceDep) -> dict:
    data = await service.get_job_with_progress(job_id)
    if not data:
        raise HTTPException(status_code=404, detail="Job not found")
    return data


@router.post("/{job_id}/cancel")
async def cancel_job(job_id: str, service: JobServiceDep) -> dict:
    cancelled = await service.cancel_job(job_id)
    if not cancelled:
        raise HTTPException(status_code=404, detail="Job not found or not cancellable")
    return {"status": "cancelled"}
