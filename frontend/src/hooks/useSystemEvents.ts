import { useEffect, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { useWebSocket } from "./useWebSocket";

interface SystemEvent {
  type: "halt_status" | "order_update" | "risk_alert";
  data: Record<string, unknown>;
}

interface HaltData {
  is_halted: boolean;
  halt_reason: string;
}

/**
 * Streams system events (halt status, order updates, risk alerts) via WebSocket.
 * Automatically invalidates relevant React Query caches on events.
 */
export function useSystemEvents() {
  const queryClient = useQueryClient();
  const { isConnected, lastMessage } = useWebSocket<SystemEvent>("/ws/system/");

  const [isHalted, setIsHalted] = useState<boolean | null>(null);
  const [haltReason, setHaltReason] = useState("");
  const [lastOrderUpdate, setLastOrderUpdate] = useState<Record<string, unknown> | null>(null);
  const [lastRiskAlert, setLastRiskAlert] = useState<Record<string, unknown> | null>(null);

  // Processing WS messages and updating local state is a valid use of
  // setState in an effect — this synchronizes external WS state into React.
  useEffect(() => {
    if (!lastMessage) return;

    switch (lastMessage.type) {
      case "halt_status": {
        const d = lastMessage.data as unknown as HaltData;
        // eslint-disable-next-line react-hooks/set-state-in-effect -- syncing external WS state
        setIsHalted(d.is_halted);
        setHaltReason(d.halt_reason ?? "");
        queryClient.invalidateQueries({ queryKey: ["risk-status"] });
        break;
      }
      case "order_update":
        setLastOrderUpdate(lastMessage.data);
        queryClient.invalidateQueries({ queryKey: ["orders"] });
        break;
      case "risk_alert":
        setLastRiskAlert(lastMessage.data);
        queryClient.invalidateQueries({ queryKey: ["risk-alerts"] });
        break;
    }
  }, [lastMessage, queryClient]);

  return { isConnected, isHalted, haltReason, lastOrderUpdate, lastRiskAlert };
}
