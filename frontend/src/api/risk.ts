import { api } from "./client";
import type { RiskStatus, RiskLimits, VaRData, HeatCheckData, RiskMetricHistoryEntry, TradeCheckLogEntry, HaltResponse, AlertLogEntry } from "../types";

export const riskApi = {
  getStatus: (portfolioId: number) =>
    api.get<RiskStatus>(`/risk/${portfolioId}/status/`),

  getLimits: (portfolioId: number) =>
    api.get<RiskLimits>(`/risk/${portfolioId}/limits/`),

  updateLimits: (portfolioId: number, limits: Partial<RiskLimits>) =>
    api.put<RiskLimits>(`/risk/${portfolioId}/limits/`, limits),

  updateEquity: (portfolioId: number, equity: number) =>
    api.post<RiskStatus>(`/risk/${portfolioId}/equity/`, { equity }),

  checkTrade: (
    portfolioId: number,
    params: {
      symbol: string;
      side: string;
      size: number;
      entry_price: number;
      stop_loss_price?: number;
    },
  ) => api.post<{ approved: boolean; reason: string }>(`/risk/${portfolioId}/check-trade/`, params),

  positionSize: (
    portfolioId: number,
    params: {
      entry_price: number;
      stop_loss_price: number;
      risk_per_trade?: number;
    },
  ) =>
    api.post<{ size: number; risk_amount: number; position_value: number }>(
      `/risk/${portfolioId}/position-size/`,
      params,
    ),

  resetDaily: (portfolioId: number) =>
    api.post<RiskStatus>(`/risk/${portfolioId}/reset-daily/`),

  getVaR: (portfolioId: number, method: string = "parametric") =>
    api.get<VaRData>(`/risk/${portfolioId}/var/?method=${method}`),

  getHeatCheck: (portfolioId: number) =>
    api.get<HeatCheckData>(`/risk/${portfolioId}/heat-check/`),

  getMetricHistory: (portfolioId: number, hours: number = 168) =>
    api.get<RiskMetricHistoryEntry[]>(`/risk/${portfolioId}/metric-history/?hours=${hours}`),

  getTradeLog: (portfolioId: number, limit: number = 50) =>
    api.get<TradeCheckLogEntry[]>(`/risk/${portfolioId}/trade-log/?limit=${limit}`),

  haltTrading: (portfolioId: number, reason: string) =>
    api.post<HaltResponse>(`/risk/${portfolioId}/halt/`, { reason }),

  resumeTrading: (portfolioId: number) =>
    api.post<HaltResponse>(`/risk/${portfolioId}/resume/`),

  getAlerts: (
    portfolioId: number,
    limit: number = 50,
    filters?: { severity?: string; event_type?: string; created_after?: string; created_before?: string },
  ) => {
    const params = new URLSearchParams({ limit: String(limit) });
    if (filters?.severity) params.set("severity", filters.severity);
    if (filters?.event_type) params.set("event_type", filters.event_type);
    if (filters?.created_after) params.set("created_after", filters.created_after);
    if (filters?.created_before) params.set("created_before", filters.created_before);
    return api.get<AlertLogEntry[]>(`/risk/${portfolioId}/alerts/?${params}`);
  },

  recordMetrics: (portfolioId: number, method: string = "parametric") =>
    api.post<RiskMetricHistoryEntry>(`/risk/${portfolioId}/record-metrics/?method=${method}`),
};
