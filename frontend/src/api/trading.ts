import { api } from "./client";
import type {
  AssetClass,
  ExchangeHealthResponse,
  LiveTradingStatus,
  Order,
  OrderCreate,
  SymbolPerformance,
  TradingMode,
  TradingPerformanceSummary,
} from "../types";

export interface PerformanceParams {
  portfolio_id?: number;
  mode?: TradingMode;
  asset_class?: AssetClass;
  date_from?: string;
  date_to?: string;
}

function perfQuery(params?: PerformanceParams): string {
  const q = new URLSearchParams();
  if (params?.portfolio_id != null) q.set("portfolio_id", String(params.portfolio_id));
  if (params?.mode) q.set("mode", params.mode);
  if (params?.asset_class) q.set("asset_class", params.asset_class);
  if (params?.date_from) q.set("date_from", params.date_from);
  if (params?.date_to) q.set("date_to", params.date_to);
  const qs = q.toString();
  return qs ? `?${qs}` : "";
}

export const tradingApi = {
  listOrders: (limit = 50, mode?: TradingMode, asset_class?: AssetClass, symbol?: string, status?: string) => {
    const params = new URLSearchParams({ limit: String(limit) });
    if (mode) params.set("mode", mode);
    if (asset_class) params.set("asset_class", asset_class);
    if (symbol) params.set("symbol", symbol);
    if (status) params.set("status", status);
    return api.get<Order[]>(`/trading/orders/?${params}`);
  },
  getOrder: (id: number) => api.get<Order>(`/trading/orders/${id}/`),
  createOrder: (data: OrderCreate) => api.post<Order>("/trading/orders/", data),
  cancelOrder: (id: number) => api.post<Order>(`/trading/orders/${id}/cancel/`),
  liveStatus: () => api.get<LiveTradingStatus>("/live-trading/status/"),
  performanceSummary: (params?: PerformanceParams) =>
    api.get<TradingPerformanceSummary>(`/trading/performance/summary/${perfQuery(params)}`),
  performanceBySymbol: (params?: PerformanceParams) =>
    api.get<SymbolPerformance[]>(`/trading/performance/by-symbol/${perfQuery(params)}`),
  cancelAll: (portfolioId: number = 1) =>
    api.post<{ cancelled: number }>("/trading/cancel-all/", { portfolio_id: portfolioId }),
  exchangeHealth: (exchangeId?: string) => {
    const params = exchangeId ? `?exchange_id=${exchangeId}` : "";
    return api.get<ExchangeHealthResponse>(`/trading/exchange-health/${params}`);
  },
};
