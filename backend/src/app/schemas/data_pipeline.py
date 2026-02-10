
from pydantic import BaseModel


class DataFileInfo(BaseModel):
    exchange: str
    symbol: str
    timeframe: str
    rows: int
    start: str | None = None
    end: str | None = None
    file: str


class DataDetailInfo(BaseModel):
    exchange: str
    symbol: str
    timeframe: str
    rows: int
    start: str | None = None
    end: str | None = None
    columns: list[str]
    file_size_mb: float


class DataDownloadRequest(BaseModel):
    symbols: list[str] = ["BTC/USDT", "ETH/USDT"]
    timeframes: list[str] = ["1h"]
    exchange: str = "binance"
    since_days: int = 365


class DataGenerateSampleRequest(BaseModel):
    symbols: list[str] = ["BTC/USDT", "ETH/USDT"]
    timeframes: list[str] = ["1h"]
    days: int = 90
