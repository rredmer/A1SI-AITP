import { api } from "./client";

export interface IndicatorData {
  symbol: string;
  timeframe: string;
  exchange: string;
  count: number;
  columns: string[];
  data: Record<string, number | null>[];
}

export const indicatorsApi = {
  list: () => api.get<string[]>("/indicators/"),

  get: (
    exchange: string,
    symbol: string,
    timeframe: string,
    indicators?: string[],
    limit?: number,
  ) => {
    const safeSymbol = symbol.replace("/", "_");
    const params = new URLSearchParams();
    if (indicators?.length) params.set("indicators", indicators.join(","));
    if (limit) params.set("limit", String(limit));
    const qs = params.toString();
    return api.get<IndicatorData>(
      `/indicators/${exchange}/${safeSymbol}/${timeframe}${qs ? `?${qs}` : ""}`,
    );
  },
};
