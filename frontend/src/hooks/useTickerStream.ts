import { useEffect, useRef, useState } from "react";
import type { TickerData } from "../types";
import { useWebSocket } from "./useWebSocket";

interface TickerMessage {
  tickers: TickerData[];
}

/**
 * Streams live ticker data via WebSocket.
 * Returns a map of symbol -> latest ticker data.
 */
export function useTickerStream() {
  const { isConnected, lastMessage } = useWebSocket<TickerMessage>(
    "/ws/market/tickers/",
  );

  const [tickers, setTickers] = useState<Record<string, TickerData>>({});
  const tickersRef = useRef(tickers);

  useEffect(() => {
    if (lastMessage?.tickers) {
      const updated = { ...tickersRef.current };
      for (const t of lastMessage.tickers) {
        updated[t.symbol] = t;
      }
      tickersRef.current = updated;
      setTickers(updated);
    }
  }, [lastMessage]);

  return { tickers, isConnected };
}
