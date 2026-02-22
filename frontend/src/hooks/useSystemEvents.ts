import { useEffect, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { useWebSocket } from "./useWebSocket";
import type { SystemEvent, OrderUpdateEvent, RiskAlertEvent } from "../types";

/**
 * Streams system events (halt status, order updates, risk alerts) via WebSocket.
 * Automatically invalidates relevant React Query caches on events.
 */
export function useSystemEvents() {
  const queryClient = useQueryClient();
  const { isConnected, lastMessage } = useWebSocket<SystemEvent>("/ws/system/");

  const [isHalted, setIsHalted] = useState<boolean | null>(null);
  const [haltReason, setHaltReason] = useState("");
  const [lastOrderUpdate, setLastOrderUpdate] = useState<OrderUpdateEvent["data"] | null>(null);
  const [lastRiskAlert, setLastRiskAlert] = useState<RiskAlertEvent["data"] | null>(null);

  // Processing WS messages and updating local state is a valid use of
  // setState in an effect — this synchronizes external WS state into React.
  useEffect(() => {
    if (!lastMessage) return;

    switch (lastMessage.type) {
      case "halt_status":
        // eslint-disable-next-line react-hooks/set-state-in-effect -- syncing external WS state
        setIsHalted(lastMessage.data.is_halted);
        setHaltReason(lastMessage.data.halt_reason ?? "");
        queryClient.invalidateQueries({ queryKey: ["risk-status"] });
        break;
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
