import { api } from "./client";
import type {
  AssetClass,
  RegimeState,
  RoutingDecision,
  RegimeHistoryEntry,
  RegimePositionSize,
} from "../types";

export const regimeApi = {
  getCurrentAll: (assetClass?: AssetClass) => {
    const params = assetClass ? `?asset_class=${assetClass}` : "";
    return api.get<RegimeState[]>(`/regime/current/${params}`);
  },

  getCurrent: (symbol: string) =>
    api.get<RegimeState>(`/regime/current/${symbol}/`),

  getHistory: (symbol: string, limit = 100) =>
    api.get<RegimeHistoryEntry[]>(`/regime/history/${symbol}/?limit=${limit}`),

  getRecommendation: (symbol: string) =>
    api.get<RoutingDecision>(`/regime/recommendation/${symbol}/`),

  getAllRecommendations: () =>
    api.get<RoutingDecision[]>("/regime/recommendations/"),

  getPositionSize: (params: {
    symbol: string;
    entry_price: number;
    stop_loss_price: number;
  }) => api.post<RegimePositionSize>("/regime/position-size/", params),
};
