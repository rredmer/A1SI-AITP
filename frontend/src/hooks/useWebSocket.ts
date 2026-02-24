import { useCallback, useEffect, useRef, useState } from "react";

interface UseWebSocketOptions {
  /** Auto-reconnect on disconnect (default: true) */
  reconnect?: boolean;
  /** Max reconnect delay in ms (default: 30000) */
  maxReconnectDelay?: number;
}

interface UseWebSocketReturn<T> {
  isConnected: boolean;
  isReconnecting: boolean;
  reconnectAttempt: number;
  lastMessage: T | null;
  send: (data: unknown) => void;
  reconnect: () => void;
}

export function useWebSocket<T = unknown>(
  path: string,
  options: UseWebSocketOptions = {},
): UseWebSocketReturn<T> {
  const { reconnect: autoReconnect = true, maxReconnectDelay = 30000 } = options;
  const [isConnected, setIsConnected] = useState(false);
  const [reconnectAttempt, setReconnectAttempt] = useState(0);
  const [lastMessage, setLastMessage] = useState<T | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttemptRef = useRef(0);
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout>>(undefined);
  const unmountedRef = useRef(false);
  const connectRef = useRef<() => void>(() => {});

  useEffect(() => {
    unmountedRef.current = false;

    function connect() {
      if (unmountedRef.current) return;

      const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
      const url = `${protocol}//${window.location.host}${path}`;
      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = () => {
        if (unmountedRef.current) {
          ws.close();
          return;
        }
        setIsConnected(true);
        reconnectAttemptRef.current = 0;
        setReconnectAttempt(0);
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data) as T;
          setLastMessage(data);
        } catch {
          // ignore non-JSON messages
        }
      };

      ws.onclose = () => {
        setIsConnected(false);
        wsRef.current = null;

        if (autoReconnect && !unmountedRef.current) {
          const delay = Math.min(
            1000 * 2 ** reconnectAttemptRef.current,
            maxReconnectDelay,
          );
          reconnectAttemptRef.current += 1;
          setReconnectAttempt(reconnectAttemptRef.current);
          reconnectTimerRef.current = setTimeout(connect, delay);
        }
      };

      ws.onerror = () => {
        // onclose will fire after onerror
      };
    }

    connectRef.current = connect;
    connect();

    return () => {
      unmountedRef.current = true;
      clearTimeout(reconnectTimerRef.current);
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [path, autoReconnect, maxReconnectDelay]);

  const send = useCallback((data: unknown) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data));
    }
  }, []);

  const manualReconnect = useCallback(() => {
    clearTimeout(reconnectTimerRef.current);
    reconnectAttemptRef.current = 0;
    setReconnectAttempt(0);
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    connectRef.current();
  }, []);

  const isReconnecting = !isConnected && autoReconnect && reconnectAttempt > 0;

  return { isConnected, isReconnecting, reconnectAttempt, lastMessage, send, reconnect: manualReconnect };
}
