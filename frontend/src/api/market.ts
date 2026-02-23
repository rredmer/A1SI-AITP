import { api } from "./client";
import type { AssetClass, TickerData, OHLCVData } from "../types";

export const marketApi = {
  ticker: (symbol: string, asset_class?: AssetClass) => {
    const params = asset_class ? `?asset_class=${asset_class}` : "";
    return api.get<TickerData>(`/market/ticker/${symbol}/${params}`);
  },
  tickers: (symbols?: string[], asset_class?: AssetClass) => {
    const parts: string[] = [];
    if (symbols) parts.push(`symbols=${symbols.join(",")}`);
    if (asset_class) parts.push(`asset_class=${asset_class}`);
    const qs = parts.length > 0 ? `?${parts.join("&")}` : "";
    return api.get<TickerData[]>(`/market/tickers/${qs}`);
  },
  ohlcv: (symbol: string, timeframe = "1h", limit = 100, asset_class?: AssetClass) => {
    const parts = [`timeframe=${timeframe}`, `limit=${limit}`];
    if (asset_class) parts.push(`asset_class=${asset_class}`);
    return api.get<OHLCVData[]>(`/market/ohlcv/${symbol}/?${parts.join("&")}`);
  },
};
