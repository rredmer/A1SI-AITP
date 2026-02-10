import asyncio

from fastapi import APIRouter, HTTPException

from app.deps import JobRunnerDep
from app.schemas.data_pipeline import (
    DataDetailInfo,
    DataDownloadRequest,
    DataFileInfo,
    DataGenerateSampleRequest,
)
from app.services.data_pipeline import DataPipelineService

router = APIRouter(prefix="/data", tags=["data"])


def _get_service() -> DataPipelineService:
    return DataPipelineService()


@router.get("/", response_model=list[DataFileInfo])
async def list_data() -> list[dict]:
    loop = asyncio.get_event_loop()
    svc = _get_service()
    return await loop.run_in_executor(None, svc.list_available_data)


@router.get("/{exchange}/{symbol}/{timeframe}", response_model=DataDetailInfo)
async def get_data_info(exchange: str, symbol: str, timeframe: str) -> dict:
    # symbol comes as e.g. "BTC_USDT" in URL, convert to "BTC/USDT"
    real_symbol = symbol.replace("_", "/")
    loop = asyncio.get_event_loop()
    svc = _get_service()
    info = await loop.run_in_executor(None, svc.get_data_info, real_symbol, timeframe, exchange)
    if not info:
        raise HTTPException(status_code=404, detail="Data file not found")
    return info


@router.post("/download", status_code=202)
async def download_data(req: DataDownloadRequest, runner: JobRunnerDep) -> dict:
    job_id = await runner.submit(
        job_type="data_download",
        run_fn=DataPipelineService.download_data,
        params=req.model_dump(),
    )
    return {"job_id": job_id, "status": "accepted"}


@router.post("/generate-sample", status_code=202)
async def generate_sample(req: DataGenerateSampleRequest, runner: JobRunnerDep) -> dict:
    job_id = await runner.submit(
        job_type="data_generate_sample",
        run_fn=DataPipelineService.generate_sample_data,
        params=req.model_dump(),
    )
    return {"job_id": job_id, "status": "accepted"}
