import { api } from "./client";
import type { AssetClass, LiveTradingStatus, Order, OrderCreate, TradingMode } from "../types";

export const tradingApi = {
  listOrders: (limit = 50, mode?: TradingMode, asset_class?: AssetClass) => {
    const params = new URLSearchParams({ limit: String(limit) });
    if (mode) params.set("mode", mode);
    if (asset_class) params.set("asset_class", asset_class);
    return api.get<Order[]>(`/trading/orders/?${params}`);
  },
  getOrder: (id: number) => api.get<Order>(`/trading/orders/${id}/`),
  createOrder: (data: OrderCreate) => api.post<Order>("/trading/orders/", data),
  cancelOrder: (id: number) => api.post<Order>(`/trading/orders/${id}/cancel/`),
  liveStatus: () => api.get<LiveTradingStatus>("/live-trading/status/"),
};
