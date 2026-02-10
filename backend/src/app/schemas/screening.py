from datetime import datetime

from pydantic import BaseModel


class ScreenRequest(BaseModel):
    symbol: str = "BTC/USDT"
    timeframe: str = "1h"
    exchange: str = "binance"
    fees: float = 0.001


class ScreenSummary(BaseModel):
    total_combos: int
    top_sharpe: float | None = None
    top_return: float | None = None


class ScreenResultRead(BaseModel):
    id: int
    job_id: str
    symbol: str
    timeframe: str
    strategy_name: str
    top_results: list | None = None
    summary: dict | None = None
    total_combinations: int
    created_at: datetime

    model_config = {"from_attributes": True}
