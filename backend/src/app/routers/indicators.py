import asyncio

from fastapi import APIRouter

from app.services.indicators import IndicatorService

router = APIRouter(prefix="/indicators", tags=["indicators"])


@router.get("/")
async def list_indicators() -> list[str]:
    return IndicatorService.list_available()


@router.get("/{exchange}/{symbol}/{timeframe}")
async def get_indicators(
    exchange: str,
    symbol: str,
    timeframe: str,
    indicators: str = "",
    limit: int = 500,
) -> dict:
    real_symbol = symbol.replace("_", "/")
    ind_list = [i.strip() for i in indicators.split(",") if i.strip()] if indicators else None
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None, IndicatorService.compute, real_symbol, timeframe, exchange, ind_list, limit
    )
