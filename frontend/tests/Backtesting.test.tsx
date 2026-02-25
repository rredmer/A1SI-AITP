import { describe, it, expect, beforeEach, vi } from "vitest";
import { screen } from "@testing-library/react";
import { Backtesting } from "../src/pages/Backtesting";
import { renderWithProviders, mockFetch } from "./helpers";

const mockStrategies = [
  { name: "CryptoInvestorV1", framework: "freqtrade", file_path: "" },
  { name: "BollingerMeanReversion", framework: "freqtrade", file_path: "" },
];

const mockResults = [
  {
    id: 1,
    job_id: "abc-123",
    framework: "freqtrade",
    strategy_name: "CryptoInvestorV1",
    symbol: "BTC/USDT",
    timeframe: "1h",
    timerange: "20250101-20250201",
    metrics: {},
    trades: [],
    config: {},
    created_at: "2026-02-10T12:00:00Z",
  },
];

describe("Backtesting Page", () => {
  beforeEach(() => {
    vi.stubGlobal(
      "fetch",
      mockFetch({
        "/api/backtest/strategies": mockStrategies,
        "/api/backtest/results": mockResults,
      }),
    );
  });

  it("renders the page heading", () => {
    renderWithProviders(<Backtesting />);
    expect(screen.getByText("Backtesting")).toBeInTheDocument();
  });

  it("renders configuration form", () => {
    renderWithProviders(<Backtesting />);
    expect(screen.getByText("Configuration")).toBeInTheDocument();
    expect(screen.getByText("Run Backtest")).toBeInTheDocument();
  });

  it("renders history table after data loads", async () => {
    renderWithProviders(<Backtesting />);
    expect(await screen.findByText("History")).toBeInTheDocument();
    const cells = await screen.findAllByText("CryptoInvestorV1");
    expect(cells.length).toBeGreaterThanOrEqual(1);
  });
});

describe("Backtesting - Configuration Form", () => {
  beforeEach(() => {
    vi.stubGlobal(
      "fetch",
      mockFetch({
        "/api/backtest/strategies": mockStrategies,
        "/api/backtest/results": mockResults,
      }),
    );
  });

  it("renders strategy dropdown", () => {
    renderWithProviders(<Backtesting />);
    const strategySelect = document.getElementById("bt-strategy");
    expect(strategySelect).toBeInTheDocument();
  });

  it("renders symbol input", () => {
    renderWithProviders(<Backtesting />);
    const symbolInput = document.getElementById("bt-symbol");
    expect(symbolInput).toBeInTheDocument();
  });

  it("renders timeframe select", () => {
    renderWithProviders(<Backtesting />);
    const timeframeSelect = document.getElementById("bt-timeframe");
    expect(timeframeSelect).toBeInTheDocument();
  });

  it("renders exchange select", () => {
    renderWithProviders(<Backtesting />);
    const exchangeSelect = document.getElementById("bt-exchange");
    expect(exchangeSelect).toBeInTheDocument();
  });

  it("renders Run Backtest button", () => {
    renderWithProviders(<Backtesting />);
    expect(screen.getByText("Run Backtest")).toBeInTheDocument();
  });

  it("renders Export CSV link in history", async () => {
    renderWithProviders(<Backtesting />);
    expect(await screen.findByText("Export CSV")).toBeInTheDocument();
  });

  it("shows empty state when no results", async () => {
    vi.stubGlobal(
      "fetch",
      mockFetch({
        "/api/backtest/strategies": mockStrategies,
        "/api/backtest/results": [],
      }),
    );
    renderWithProviders(<Backtesting />);
    expect(await screen.findByText("History")).toBeInTheDocument();
  });

  it("framework buttons have aria-labels", () => {
    renderWithProviders(<Backtesting />);
    const buttons = screen.getAllByRole("button");
    const fwButtons = buttons.filter(btn => btn.getAttribute("aria-label")?.includes("Select"));
    expect(fwButtons.length).toBeGreaterThan(0);
  });

  it("refresh history button has aria-label", async () => {
    renderWithProviders(<Backtesting />);
    const btn = await screen.findByLabelText("Refresh history");
    expect(btn).toBeInTheDocument();
  });
});
