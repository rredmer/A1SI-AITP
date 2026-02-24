import { useQuery } from "@tanstack/react-query";
import { tradingApi } from "../api/trading";

interface ExchangeHealthBadgeProps {
  exchangeId?: string;
}

export function ExchangeHealthBadge({ exchangeId }: ExchangeHealthBadgeProps) {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["exchange-health", exchangeId],
    queryFn: () => tradingApi.exchangeHealth(exchangeId),
    refetchInterval: 30_000,
  });

  if (isLoading) {
    return (
      <span className="inline-flex items-center gap-1.5 text-xs text-[var(--color-text-muted)]">
        <span className="inline-block h-2 w-2 rounded-full bg-gray-400" data-testid="health-dot-loading" />
        Checking...
      </span>
    );
  }

  if (isError || !data) {
    return (
      <span
        className="inline-flex items-center gap-1.5 text-xs text-red-400"
        title="Failed to check exchange health"
      >
        <span className="inline-block h-2 w-2 rounded-full bg-red-500" data-testid="health-dot-error" />
        Disconnected
      </span>
    );
  }

  const connected = data.connected ?? false;
  const latency = data.latency_ms ?? 0;
  const exchangeName = data.exchange ?? "Exchange";

  if (!connected) {
    return (
      <span
        className="inline-flex items-center gap-1.5 text-xs text-red-400"
        title={data.error ?? "Exchange disconnected"}
      >
        <span className="inline-block h-2 w-2 rounded-full bg-red-500" data-testid="health-dot-disconnected" />
        Disconnected
      </span>
    );
  }

  const latencyColor =
    latency < 500 ? "text-green-400" : latency < 1000 ? "text-yellow-400" : "text-red-400";

  return (
    <span className="inline-flex items-center gap-1.5 text-xs">
      <span className="inline-block h-2 w-2 rounded-full bg-green-500" data-testid="health-dot-connected" />
      <span className="text-[var(--color-text-muted)]">{exchangeName}</span>
      <span className={latencyColor}>{latency}ms</span>
    </span>
  );
}
