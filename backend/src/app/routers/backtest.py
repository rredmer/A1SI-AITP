from fastapi import APIRouter, HTTPException

from app.deps import JobRunnerDep, SessionDep
from app.schemas.backtest import BacktestRequest, BacktestResultRead, StrategyInfo
from app.services.backtest import BacktestService

router = APIRouter(prefix="/backtest", tags=["backtest"])


@router.post("/run", status_code=202)
async def run_backtest(req: BacktestRequest, runner: JobRunnerDep) -> dict:
    job_id = await runner.submit(
        job_type="backtest",
        run_fn=BacktestService.run_backtest,
        params=req.model_dump(),
    )
    return {"job_id": job_id, "status": "accepted"}


@router.get("/results", response_model=list[BacktestResultRead])
async def list_results(session: SessionDep, limit: int = 20) -> list:
    svc = BacktestService(session)
    return await svc.list_results(limit)


@router.get("/results/{result_id}", response_model=BacktestResultRead)
async def get_result(result_id: int, session: SessionDep) -> object:
    svc = BacktestService(session)
    result = await svc.get_result(result_id)
    if not result:
        raise HTTPException(status_code=404, detail="Backtest result not found")
    return result


@router.get("/strategies", response_model=list[StrategyInfo])
async def list_strategies() -> list[dict]:
    return BacktestService.list_strategies()


@router.get("/compare")
async def compare_results(ids: str, session: SessionDep) -> list:
    id_list = [int(x) for x in ids.split(",") if x.strip()]
    svc = BacktestService(session)
    results = await svc.compare_results(id_list)
    return [BacktestResultRead.model_validate(r) for r in results]
