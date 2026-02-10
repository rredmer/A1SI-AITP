import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { riskApi } from "../api/risk";
import type { RiskLimits, RiskStatus } from "../types";

export function RiskManagement() {
  const queryClient = useQueryClient();
  const [portfolioId, setPortfolioId] = useState(1);

  const { data: status } = useQuery<RiskStatus>({
    queryKey: ["risk-status", portfolioId],
    queryFn: () => riskApi.getStatus(portfolioId),
  });

  const { data: limits } = useQuery<RiskLimits>({
    queryKey: ["risk-limits", portfolioId],
    queryFn: () => riskApi.getLimits(portfolioId),
  });

  // Position sizer state
  const [entryPrice, setEntryPrice] = useState(50000);
  const [stopLoss, setStopLoss] = useState(48000);
  const [posResult, setPosResult] = useState<{ size: number; risk_amount: number; position_value: number } | null>(null);

  const positionMutation = useMutation({
    mutationFn: () => riskApi.positionSize(portfolioId, { entry_price: entryPrice, stop_loss_price: stopLoss }),
    onSuccess: (data) => setPosResult(data),
  });

  // Trade checker state
  const [tradeSymbol, setTradeSymbol] = useState("BTC/USDT");
  const [tradeSide, setTradeSide] = useState("buy");
  const [tradeSize, setTradeSize] = useState(0.1);
  const [tradeEntry, setTradeEntry] = useState(50000);
  const [tradeResult, setTradeResult] = useState<{ approved: boolean; reason: string } | null>(null);

  const tradeMutation = useMutation({
    mutationFn: () =>
      riskApi.checkTrade(portfolioId, {
        symbol: tradeSymbol,
        side: tradeSide,
        size: tradeSize,
        entry_price: tradeEntry,
      }),
    onSuccess: (data) => setTradeResult(data),
  });

  const resetMutation = useMutation({
    mutationFn: () => riskApi.resetDaily(portfolioId),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: ["risk-status", portfolioId] }),
  });

  const drawdownPct = status ? (status.drawdown * 100).toFixed(2) : "0.00";
  const drawdownColor = status
    ? status.drawdown > 0.1
      ? "text-red-400"
      : status.drawdown > 0.05
        ? "text-yellow-400"
        : "text-green-400"
    : "text-[var(--color-text-muted)]";

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <h2 className="text-2xl font-bold">Risk Management</h2>
        <div className="flex items-center gap-2">
          <label className="text-sm text-[var(--color-text-muted)]">Portfolio ID:</label>
          <input
            type="number"
            value={portfolioId}
            onChange={(e) => setPortfolioId(Number(e.target.value))}
            className="w-20 rounded-lg border border-[var(--color-border)] bg-[var(--color-bg)] px-2 py-1 text-sm"
          />
        </div>
      </div>

      {/* Status Cards */}
      <div className="mb-6 grid grid-cols-2 gap-4 md:grid-cols-4">
        <StatusCard label="Equity" value={`$${(status?.equity ?? 0).toLocaleString()}`} />
        <StatusCard label="Drawdown" value={`${drawdownPct}%`} className={drawdownColor} />
        <StatusCard label="Daily PnL" value={`$${(status?.daily_pnl ?? 0).toFixed(2)}`}
          className={status && status.daily_pnl >= 0 ? "text-green-400" : "text-red-400"} />
        <StatusCard
          label="Status"
          value={status?.is_halted ? "HALTED" : "Active"}
          className={status?.is_halted ? "text-red-400" : "text-green-400"}
        />
      </div>

      {status?.is_halted && (
        <div className="mb-6 rounded-lg border border-red-500/30 bg-red-500/10 p-3 text-sm text-red-400">
          Trading halted: {status.halt_reason}
          <button
            onClick={() => resetMutation.mutate()}
            className="ml-3 rounded bg-red-500/20 px-2 py-1 text-xs hover:bg-red-500/30"
          >
            Reset Daily
          </button>
        </div>
      )}

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Limits Config */}
        <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6">
          <h3 className="mb-4 text-lg font-semibold">Risk Limits</h3>
          {limits && (
            <div className="space-y-2 text-sm">
              <LimitRow label="Max Drawdown" value={`${(limits.max_portfolio_drawdown * 100).toFixed(1)}%`} />
              <LimitRow label="Single Trade Risk" value={`${(limits.max_single_trade_risk * 100).toFixed(1)}%`} />
              <LimitRow label="Max Daily Loss" value={`${(limits.max_daily_loss * 100).toFixed(1)}%`} />
              <LimitRow label="Max Open Positions" value={String(limits.max_open_positions)} />
              <LimitRow label="Max Position Size" value={`${(limits.max_position_size_pct * 100).toFixed(1)}%`} />
              <LimitRow label="Min Risk/Reward" value={String(limits.min_risk_reward)} />
              <LimitRow label="Max Leverage" value={`${limits.max_leverage}x`} />
            </div>
          )}
        </div>

        {/* Position Sizer */}
        <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6">
          <h3 className="mb-4 text-lg font-semibold">Position Sizer</h3>
          <div className="space-y-3">
            <div>
              <label className="mb-1 block text-xs text-[var(--color-text-muted)]">Entry Price</label>
              <input
                type="number"
                value={entryPrice}
                onChange={(e) => setEntryPrice(Number(e.target.value))}
                className="w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-bg)] px-3 py-2 text-sm"
              />
            </div>
            <div>
              <label className="mb-1 block text-xs text-[var(--color-text-muted)]">Stop Loss</label>
              <input
                type="number"
                value={stopLoss}
                onChange={(e) => setStopLoss(Number(e.target.value))}
                className="w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-bg)] px-3 py-2 text-sm"
              />
            </div>
            <button
              onClick={() => positionMutation.mutate()}
              className="w-full rounded-lg bg-[var(--color-primary)] px-4 py-2 text-sm font-medium text-white"
            >
              Calculate
            </button>
            {posResult && (
              <div className="mt-2 space-y-1 rounded-lg bg-[var(--color-bg)] p-3 text-sm">
                <div className="flex justify-between"><span className="text-[var(--color-text-muted)]">Size:</span> <span className="font-mono">{posResult.size}</span></div>
                <div className="flex justify-between"><span className="text-[var(--color-text-muted)]">Risk Amount:</span> <span className="font-mono">${posResult.risk_amount}</span></div>
                <div className="flex justify-between"><span className="text-[var(--color-text-muted)]">Position Value:</span> <span className="font-mono">${posResult.position_value}</span></div>
              </div>
            )}
          </div>
        </div>

        {/* Trade Checker */}
        <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6">
          <h3 className="mb-4 text-lg font-semibold">Trade Checker</h3>
          <div className="space-y-3">
            <div>
              <label className="mb-1 block text-xs text-[var(--color-text-muted)]">Symbol</label>
              <input
                value={tradeSymbol}
                onChange={(e) => setTradeSymbol(e.target.value)}
                className="w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-bg)] px-3 py-2 text-sm"
              />
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => setTradeSide("buy")}
                className={`flex-1 rounded-lg px-3 py-2 text-sm font-medium ${tradeSide === "buy" ? "bg-green-500 text-white" : "bg-[var(--color-bg)] text-[var(--color-text-muted)]"}`}
              >
                Buy
              </button>
              <button
                onClick={() => setTradeSide("sell")}
                className={`flex-1 rounded-lg px-3 py-2 text-sm font-medium ${tradeSide === "sell" ? "bg-red-500 text-white" : "bg-[var(--color-bg)] text-[var(--color-text-muted)]"}`}
              >
                Sell
              </button>
            </div>
            <div className="grid grid-cols-2 gap-2">
              <div>
                <label className="mb-1 block text-xs text-[var(--color-text-muted)]">Size</label>
                <input
                  type="number"
                  step="0.01"
                  value={tradeSize}
                  onChange={(e) => setTradeSize(Number(e.target.value))}
                  className="w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-bg)] px-3 py-2 text-sm"
                />
              </div>
              <div>
                <label className="mb-1 block text-xs text-[var(--color-text-muted)]">Entry</label>
                <input
                  type="number"
                  value={tradeEntry}
                  onChange={(e) => setTradeEntry(Number(e.target.value))}
                  className="w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-bg)] px-3 py-2 text-sm"
                />
              </div>
            </div>
            <button
              onClick={() => tradeMutation.mutate()}
              className="w-full rounded-lg bg-[var(--color-primary)] px-4 py-2 text-sm font-medium text-white"
            >
              Check Trade
            </button>
            {tradeResult && (
              <div
                className={`mt-2 rounded-lg p-3 text-sm ${tradeResult.approved ? "bg-green-500/10 text-green-400" : "bg-red-500/10 text-red-400"}`}
              >
                <span className="font-medium">{tradeResult.approved ? "Approved" : "Rejected"}</span>
                : {tradeResult.reason}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function StatusCard({ label, value, className = "" }: { label: string; value: string; className?: string }) {
  return (
    <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-4">
      <p className="text-xs text-[var(--color-text-muted)]">{label}</p>
      <p className={`text-xl font-bold ${className}`}>{value}</p>
    </div>
  );
}

function LimitRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between">
      <span className="text-[var(--color-text-muted)]">{label}</span>
      <span className="font-mono">{value}</span>
    </div>
  );
}
