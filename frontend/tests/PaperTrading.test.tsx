import { describe, it, expect, beforeEach, vi } from "vitest";
import { screen } from "@testing-library/react";
import { PaperTrading } from "../src/pages/PaperTrading";
import { renderWithProviders, mockFetch } from "./helpers";

const stoppedStatus = {
  running: false,
  strategy: null,
  pid: null,
  started_at: null,
  uptime_seconds: 0,
  exit_code: null,
};

const runningStatus = {
  running: true,
  strategy: "CryptoInvestorV1",
  pid: 12345,
  started_at: "2026-02-15T10:00:00Z",
  uptime_seconds: 3600,
  exit_code: null,
};

const mockStrategies = [
  { name: "CryptoInvestorV1", framework: "freqtrade", file_path: "" },
  { name: "BollingerMeanReversion", framework: "freqtrade", file_path: "" },
  { name: "VolatilityBreakout", framework: "freqtrade", file_path: "" },
];

describe("PaperTrading - Stopped State", () => {
  beforeEach(() => {
    vi.stubGlobal(
      "fetch",
      mockFetch({
        "/api/paper-trading/status": stoppedStatus,
        "/api/paper-trading/log": [],
        "/api/backtest/strategies": mockStrategies,
      }),
    );
  });

  it("renders the page heading", () => {
    renderWithProviders(<PaperTrading />);
    expect(screen.getByText("Paper Trading")).toBeInTheDocument();
  });

  it("shows Stopped status", async () => {
    renderWithProviders(<PaperTrading />);
    expect(await screen.findByText("Stopped")).toBeInTheDocument();
  });

  it("shows Start button when stopped", async () => {
    renderWithProviders(<PaperTrading />);
    expect(await screen.findByText("Start")).toBeInTheDocument();
  });

  it("shows strategy selector when stopped", async () => {
    renderWithProviders(<PaperTrading />);
    const select = await screen.findByRole("combobox");
    expect(select).toBeInTheDocument();
  });

  it("renders stat cards", () => {
    renderWithProviders(<PaperTrading />);
    expect(screen.getByText("Total Profit")).toBeInTheDocument();
    expect(screen.getByText("Win Rate")).toBeInTheDocument();
    expect(screen.getByText("Trades")).toBeInTheDocument();
    expect(screen.getByText("Closed P/L")).toBeInTheDocument();
  });
});

describe("PaperTrading - Running State", () => {
  beforeEach(() => {
    vi.stubGlobal(
      "fetch",
      mockFetch({
        "/api/paper-trading/status": runningStatus,
        "/api/paper-trading/trades": [],
        "/api/paper-trading/profit": {
          profit_all_coin: 0.05,
          profit_all_percent: 2.5,
          profit_closed_coin: 0.03,
          profit_closed_percent: 1.8,
          trade_count: 5,
          closed_trade_count: 3,
          winning_trades: 2,
          losing_trades: 1,
        },
        "/api/paper-trading/performance": [
          { pair: "BTC/USDT", profit: 1.5, count: 3 },
        ],
        "/api/paper-trading/history": [],
        "/api/paper-trading/log": [
          { timestamp: "2026-02-15T10:00:00Z", event: "started", strategy: "CryptoInvestorV1" },
        ],
        "/api/backtest/strategies": mockStrategies,
      }),
    );
  });

  it("shows Running status", async () => {
    renderWithProviders(<PaperTrading />);
    expect(await screen.findByText("Running")).toBeInTheDocument();
  });

  it("shows Stop button when running", async () => {
    renderWithProviders(<PaperTrading />);
    expect(await screen.findByText("Stop")).toBeInTheDocument();
  });

  it("shows strategy name in status bar", async () => {
    renderWithProviders(<PaperTrading />);
    const matches = await screen.findAllByText("CryptoInvestorV1");
    expect(matches.length).toBeGreaterThanOrEqual(1);
  });

  it("renders open trades section", async () => {
    renderWithProviders(<PaperTrading />);
    expect(await screen.findByText("Open Trades")).toBeInTheDocument();
  });

  it("renders performance section", async () => {
    renderWithProviders(<PaperTrading />);
    expect(await screen.findByText("Performance by Pair")).toBeInTheDocument();
  });

  it("renders event log section", async () => {
    renderWithProviders(<PaperTrading />);
    expect(await screen.findByText("Event Log")).toBeInTheDocument();
  });
});
