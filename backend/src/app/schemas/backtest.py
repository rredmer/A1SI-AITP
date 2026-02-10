from datetime import datetime

from pydantic import BaseModel


class BacktestRequest(BaseModel):
    framework: str = "freqtrade"  # freqtrade / nautilus
    strategy: str = "SampleStrategy"
    symbol: str = "BTC/USDT"
    timeframe: str = "1h"
    timerange: str = ""
    exchange: str = "binance"


class StrategyInfo(BaseModel):
    name: str
    framework: str
    file_path: str


class BacktestResultRead(BaseModel):
    id: int
    job_id: str
    framework: str
    strategy_name: str
    symbol: str
    timeframe: str
    timerange: str
    metrics: dict | None = None
    trades: list | None = None
    config: dict | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
