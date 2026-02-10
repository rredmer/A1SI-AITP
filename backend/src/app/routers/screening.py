from fastapi import APIRouter, HTTPException

from app.deps import JobRunnerDep, SessionDep
from app.schemas.screening import ScreenRequest, ScreenResultRead
from app.services.screener import STRATEGY_TYPES, ScreenerService

router = APIRouter(prefix="/screening", tags=["screening"])


@router.post("/run", status_code=202)
async def run_screen(req: ScreenRequest, runner: JobRunnerDep) -> dict:
    job_id = await runner.submit(
        job_type="screening",
        run_fn=ScreenerService.run_full_screen,
        params=req.model_dump(),
    )
    return {"job_id": job_id, "status": "accepted"}


@router.get("/results", response_model=list[ScreenResultRead])
async def list_results(session: SessionDep, limit: int = 20) -> list:
    svc = ScreenerService(session)
    return await svc.list_results(limit)


@router.get("/results/{result_id}", response_model=ScreenResultRead)
async def get_result(result_id: int, session: SessionDep) -> object:
    svc = ScreenerService(session)
    result = await svc.get_result(result_id)
    if not result:
        raise HTTPException(status_code=404, detail="Screen result not found")
    return result


@router.get("/strategies")
async def list_strategies() -> list[dict]:
    return STRATEGY_TYPES
