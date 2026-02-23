import { api } from "./client";
import type { AssetClass, DataFileInfo } from "../types";

export const dataApi = {
  list: (asset_class?: AssetClass) => {
    const qs = asset_class ? `?asset_class=${asset_class}` : "";
    return api.get<DataFileInfo[]>(`/data/${qs}`);
  },

  getInfo: (exchange: string, symbol: string, timeframe: string) => {
    const safeSymbol = symbol.replace("/", "_");
    return api.get<DataFileInfo>(`/data/${exchange}/${safeSymbol}/${timeframe}/`);
  },

  download: (params: {
    symbols: string[];
    timeframes: string[];
    exchange: string;
    since_days: number;
    asset_class?: AssetClass;
  }) => api.post<{ job_id: string }>("/data/download/", params),

  generateSample: (params: {
    symbols: string[];
    timeframes: string[];
    days: number;
  }) => api.post<{ job_id: string }>("/data/generate-sample/", params),
};
