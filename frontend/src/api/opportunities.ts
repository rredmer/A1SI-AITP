import { api } from "./client";
import type { AssetClass, DailyReport, MarketOpportunity, OpportunitySummary } from "../types";

export const opportunitiesApi = {
  list: (params?: { type?: string; min_score?: number; limit?: number; asset_class?: AssetClass }) => {
    const parts: string[] = [];
    if (params?.type) parts.push(`type=${params.type}`);
    if (params?.min_score) parts.push(`min_score=${params.min_score}`);
    if (params?.limit) parts.push(`limit=${params.limit}`);
    if (params?.asset_class) parts.push(`asset_class=${params.asset_class}`);
    const qs = parts.length > 0 ? `?${parts.join("&")}` : "";
    return api.get<MarketOpportunity[]>(`/market/opportunities/${qs}`);
  },
  summary: (asset_class?: AssetClass) => {
    const qs = asset_class ? `?asset_class=${asset_class}` : "";
    return api.get<OpportunitySummary>(`/market/opportunities/summary/${qs}`);
  },
  dailyReport: () => api.get<DailyReport>("/market/daily-report/"),
  dailyReportHistory: (limit = 30) =>
    api.get<DailyReport[]>(`/market/daily-report/history/?limit=${limit}`),
};
