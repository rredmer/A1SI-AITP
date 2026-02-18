import { api } from "./client";
import type { LiveTradingStatus, Order, TradingMode } from "../types";

export const tradingApi = {
  listOrders: (limit = 50, mode?: TradingMode) => {
    const params = new URLSearchParams({ limit: String(limit) });
    if (mode) params.set("mode", mode);
    return api.get<Order[]>(`/trading/orders?${params}`);
  },
  getOrder: (id: number) => api.get<Order>(`/trading/orders/${id}`),
  createOrder: (data: {
    symbol: string;
    side: "buy" | "sell";
    order_type?: string;
    amount: number;
    price?: number;
    exchange_id?: string;
    mode?: TradingMode;
    portfolio_id?: number;
    stop_loss_price?: number;
  }) => api.post<Order>("/trading/orders", data),
  cancelOrder: (id: number) => api.post<Order>(`/trading/orders/${id}/cancel`),
  liveStatus: () => api.get<LiveTradingStatus>("/live-trading/status"),
};
