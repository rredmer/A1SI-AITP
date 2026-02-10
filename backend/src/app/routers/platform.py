import asyncio

from fastapi import APIRouter

from app.deps import SessionDep
from app.services.platform_status import PlatformStatusService

router = APIRouter(prefix="/platform", tags=["platform"])


@router.get("/status")
async def get_status(session: SessionDep) -> dict:
    svc = PlatformStatusService(session)
    return await svc.get_full_status()


@router.get("/config")
async def get_config() -> dict:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, PlatformStatusService.get_platform_config)
