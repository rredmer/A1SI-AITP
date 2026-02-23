import type { AssetClass } from "../types";

export const DEFAULT_SYMBOLS: Record<AssetClass, string[]> = {
  crypto: ["BTC/USDT", "ETH/USDT", "SOL/USDT", "BNB/USDT", "XRP/USDT"],
  equity: ["AAPL/USD", "MSFT/USD", "GOOGL/USD", "AMZN/USD", "SPY/USD"],
  forex: ["EUR/USD", "GBP/USD", "USD/JPY", "AUD/USD", "EUR/GBP"],
};

export const DEFAULT_SYMBOL: Record<AssetClass, string> = {
  crypto: "BTC/USDT",
  equity: "AAPL/USD",
  forex: "EUR/USD",
};

export const EXCHANGE_OPTIONS: Record<AssetClass, { value: string; label: string }[]> = {
  crypto: [
    { value: "binance", label: "Binance" },
    { value: "coinbase", label: "Coinbase" },
    { value: "kraken", label: "Kraken" },
    { value: "bybit", label: "Bybit" },
  ],
  equity: [{ value: "yfinance", label: "Yahoo Finance" }],
  forex: [{ value: "yfinance", label: "Yahoo Finance" }],
};

export const TIMEFRAME_OPTIONS: Record<AssetClass, { value: string; label: string }[]> = {
  crypto: [
    { value: "1m", label: "1m" },
    { value: "5m", label: "5m" },
    { value: "15m", label: "15m" },
    { value: "1h", label: "1h" },
    { value: "4h", label: "4h" },
    { value: "1d", label: "1d" },
  ],
  equity: [
    { value: "1h", label: "1h" },
    { value: "1d", label: "1d" },
  ],
  forex: [
    { value: "5m", label: "5m" },
    { value: "15m", label: "15m" },
    { value: "1h", label: "1h" },
    { value: "4h", label: "4h" },
    { value: "1d", label: "1d" },
  ],
};

export const BACKTEST_FRAMEWORKS: Record<AssetClass, { value: string; label: string }[]> = {
  crypto: [
    { value: "freqtrade", label: "Freqtrade" },
    { value: "nautilus", label: "NautilusTrader" },
    { value: "hft", label: "HFT Backtest" },
  ],
  equity: [{ value: "nautilus", label: "NautilusTrader" }],
  forex: [{ value: "nautilus", label: "NautilusTrader" }],
};

export const ASSET_CLASS_LABELS: Record<AssetClass, string> = {
  crypto: "Crypto",
  equity: "Equities",
  forex: "Forex",
};

export const ASSET_CLASS_COLORS: Record<AssetClass, string> = {
  crypto: "orange",
  equity: "blue",
  forex: "green",
};

export const DEFAULT_FEES: Record<AssetClass, number> = {
  crypto: 0.001,
  equity: 0.0,
  forex: 0.0001,
};
