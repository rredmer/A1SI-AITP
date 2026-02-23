import { api } from "./client";
import type { AssetClass, ScreenResult } from "../types";

export const screeningApi = {
  run: (params: {
    symbol: string;
    timeframe: string;
    exchange: string;
    fees: number;
    asset_class?: AssetClass;
  }) => api.post<{ job_id: string }>("/screening/run/", params),

  results: (limit?: number) =>
    api.get<ScreenResult[]>(`/screening/results/${limit ? `?limit=${limit}` : ""}`),

  result: (id: number) => api.get<ScreenResult>(`/screening/results/${id}/`),

  strategies: () =>
    api.get<{ name: string; label: string; description: string }[]>("/screening/strategies/"),
};
