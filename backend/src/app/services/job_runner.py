"""
Job runner — dispatches sync functions to a thread pool, tracks progress in-memory,
and persists job state to DB.
"""

import logging
import uuid
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.models.job import BackgroundJob

logger = logging.getLogger("job_runner")

# In-memory progress store for live polling (avoids DB writes on every progress tick)
_job_progress: dict[str, dict[str, Any]] = {}


class JobRunner:
    """Manages background job execution via ThreadPoolExecutor."""

    def __init__(self, session_factory: async_sessionmaker, max_workers: int = 2):
        self._session_factory = session_factory
        self._executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="job")

    async def submit(
        self,
        job_type: str,
        run_fn: Callable[..., Any],
        params: dict | None = None,
    ) -> str:
        """Create a DB job record and dispatch run_fn to the thread pool."""
        job_id = str(uuid.uuid4())

        async with self._session_factory() as session:
            job = BackgroundJob(
                id=job_id,
                job_type=job_type,
                status="pending",
                params=params,
            )
            session.add(job)
            await session.commit()

        _job_progress[job_id] = {"progress": 0.0, "progress_message": "Queued"}

        # Submit to thread pool
        self._executor.submit(self._run_job, job_id, run_fn, params or {})
        return job_id

    def _run_job(self, job_id: str, run_fn: Callable, params: dict) -> None:
        """Execute the sync function in a worker thread."""
        import asyncio

        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(self._update_job_status(job_id, "running"))
            _job_progress[job_id] = {"progress": 0.0, "progress_message": "Running"}

            def progress_callback(progress: float, message: str = "") -> None:
                _job_progress[job_id] = {
                    "progress": min(progress, 1.0),
                    "progress_message": message,
                }

            result = run_fn(params, progress_callback)

            _job_progress[job_id] = {"progress": 1.0, "progress_message": "Complete"}
            loop.run_until_complete(
                self._complete_job(job_id, result=result)
            )
        except Exception as e:
            logger.exception(f"Job {job_id} failed: {e}")
            _job_progress[job_id] = {"progress": 0.0, "progress_message": f"Failed: {e}"}
            loop.run_until_complete(
                self._complete_job(job_id, error=str(e))
            )
        finally:
            loop.close()

    async def _update_job_status(self, job_id: str, status: str) -> None:
        async with self._session_factory() as session:
            stmt = (
                update(BackgroundJob)
                .where(BackgroundJob.id == job_id)
                .values(status=status, started_at=datetime.now(timezone.utc))
            )
            await session.execute(stmt)
            await session.commit()

    async def _complete_job(
        self,
        job_id: str,
        result: Any = None,
        error: str | None = None,
    ) -> None:
        async with self._session_factory() as session:
            values: dict[str, Any] = {
                "status": "failed" if error else "completed",
                "completed_at": datetime.now(timezone.utc),
                "progress": 1.0 if not error else 0.0,
            }
            if result is not None:
                values["result"] = result
            if error is not None:
                values["error"] = error

            stmt = (
                update(BackgroundJob)
                .where(BackgroundJob.id == job_id)
                .values(**values)
            )
            await session.execute(stmt)
            await session.commit()

        # Clean up old progress after a delay (keep for polling)
        # Progress entry stays until next submit or server restart

    @staticmethod
    def get_live_progress(job_id: str) -> dict[str, Any] | None:
        """Get in-memory progress for a running job."""
        return _job_progress.get(job_id)

    async def get_job(self, job_id: str) -> BackgroundJob | None:
        async with self._session_factory() as session:
            result = await session.execute(
                select(BackgroundJob).where(BackgroundJob.id == job_id)
            )
            return result.scalar_one_or_none()

    async def cancel_job(self, job_id: str) -> bool:
        """Mark a job as cancelled (does not interrupt running thread)."""
        async with self._session_factory() as session:
            stmt = (
                update(BackgroundJob)
                .where(
                    BackgroundJob.id == job_id,
                    BackgroundJob.status.in_(["pending", "running"]),
                )
                .values(status="cancelled", completed_at=datetime.now(timezone.utc))
            )
            result = await session.execute(stmt)
            await session.commit()
            return result.rowcount > 0  # type: ignore[return-value]
