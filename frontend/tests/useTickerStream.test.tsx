import { describe, it, expect, vi } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useTickerStream } from "../src/hooks/useTickerStream";

let lastWebSocketResult = {
  isConnected: false,
  lastMessage: null as unknown,
  send: vi.fn(),
};

vi.mock("../src/hooks/useWebSocket", () => ({
  useWebSocket: () => lastWebSocketResult,
}));

describe("useTickerStream", () => {
  beforeEach(() => {
    lastWebSocketResult = {
      isConnected: false,
      lastMessage: null,
      send: vi.fn(),
    };
  });

  it("returns empty tickers initially", () => {
    const { result } = renderHook(() => useTickerStream());

    expect(result.current.tickers).toEqual({});
    expect(result.current.isConnected).toBe(false);
  });

  it("reflects connection status", () => {
    lastWebSocketResult.isConnected = true;

    const { result } = renderHook(() => useTickerStream());

    expect(result.current.isConnected).toBe(true);
  });

  it("accumulates ticker data from messages", () => {
    lastWebSocketResult.lastMessage = {
      tickers: [
        { symbol: "BTC/USDT", price: 50000, volume_24h: 1000, change_24h: 2.5 },
        { symbol: "ETH/USDT", price: 3000, volume_24h: 500, change_24h: -1.2 },
      ],
    };

    const { result } = renderHook(() => useTickerStream());

    expect(result.current.tickers["BTC/USDT"]).toEqual({
      symbol: "BTC/USDT",
      price: 50000,
      volume_24h: 1000,
      change_24h: 2.5,
    });
    expect(result.current.tickers["ETH/USDT"]).toEqual({
      symbol: "ETH/USDT",
      price: 3000,
      volume_24h: 500,
      change_24h: -1.2,
    });
  });

  it("updates existing ticker data", () => {
    lastWebSocketResult.lastMessage = {
      tickers: [
        { symbol: "BTC/USDT", price: 50000, volume_24h: 1000, change_24h: 2.5 },
      ],
    };

    const { result, rerender } = renderHook(() => useTickerStream());

    expect(result.current.tickers["BTC/USDT"].price).toBe(50000);

    // Simulate price update
    act(() => {
      lastWebSocketResult.lastMessage = {
        tickers: [
          { symbol: "BTC/USDT", price: 51000, volume_24h: 1100, change_24h: 4.5 },
        ],
      };
    });

    rerender();

    expect(result.current.tickers["BTC/USDT"].price).toBe(51000);
  });

  it("preserves existing tickers when new ones arrive", () => {
    lastWebSocketResult.lastMessage = {
      tickers: [
        { symbol: "BTC/USDT", price: 50000, volume_24h: 1000, change_24h: 2.5 },
      ],
    };

    const { result, rerender } = renderHook(() => useTickerStream());

    expect(Object.keys(result.current.tickers)).toHaveLength(1);

    act(() => {
      lastWebSocketResult.lastMessage = {
        tickers: [
          { symbol: "ETH/USDT", price: 3000, volume_24h: 500, change_24h: -1.0 },
        ],
      };
    });

    rerender();

    expect(Object.keys(result.current.tickers)).toHaveLength(2);
    expect(result.current.tickers["BTC/USDT"]).toBeDefined();
    expect(result.current.tickers["ETH/USDT"]).toBeDefined();
  });

  it("ignores messages without tickers field", () => {
    lastWebSocketResult.lastMessage = { type: "heartbeat" };

    const { result } = renderHook(() => useTickerStream());

    expect(result.current.tickers).toEqual({});
  });

  it("handles null message", () => {
    lastWebSocketResult.lastMessage = null;

    const { result } = renderHook(() => useTickerStream());

    expect(result.current.tickers).toEqual({});
  });
});
