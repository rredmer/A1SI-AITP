"""Job service — async CRUD for background jobs."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job import BackgroundJob
from app.services.job_runner import JobRunner


class JobService:
    def __init__(self, session: AsyncSession, runner: JobRunner):
        self._session = session
        self._runner = runner

    async def list_jobs(
        self, job_type: str | None = None, limit: int = 50
    ) -> list[BackgroundJob]:
        stmt = select(BackgroundJob).order_by(BackgroundJob.created_at.desc()).limit(limit)
        if job_type:
            stmt = stmt.where(BackgroundJob.job_type == job_type)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_job(self, job_id: str) -> BackgroundJob | None:
        result = await self._session.execute(
            select(BackgroundJob).where(BackgroundJob.id == job_id)
        )
        return result.scalar_one_or_none()

    async def get_job_with_progress(self, job_id: str) -> dict | None:
        job = await self.get_job(job_id)
        if not job:
            return None
        data = {
            "id": job.id,
            "job_type": job.job_type,
            "status": job.status,
            "progress": job.progress,
            "progress_message": job.progress_message,
            "params": job.params,
            "result": job.result,
            "error": job.error,
            "started_at": job.started_at,
            "completed_at": job.completed_at,
            "created_at": job.created_at,
        }
        # Overlay live progress from memory if job is still running
        live = JobRunner.get_live_progress(job_id)
        if live and job.status in ("pending", "running"):
            data["progress"] = live["progress"]
            data["progress_message"] = live["progress_message"]
        return data

    async def cancel_job(self, job_id: str) -> bool:
        return await self._runner.cancel_job(job_id)
