import { useEffect, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { useWebSocket } from "./useWebSocket";
import { useToast } from "./useToast";
import type {
  SystemEvent,
  OrderUpdateEvent,
  RiskAlertEvent,
  RegimeChangeEvent,
  SchedulerEventData,
} from "../types";

/**
 * Streams system events (halt status, order updates, risk alerts, news,
 * sentiment, scheduler, regime changes) via WebSocket.
 * Automatically invalidates relevant React Query caches on events.
 */
export function useSystemEvents() {
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const { isConnected, lastMessage } = useWebSocket<SystemEvent>("/ws/system/");

  const [isHalted, setIsHalted] = useState<boolean | null>(null);
  const [haltReason, setHaltReason] = useState("");
  const [lastOrderUpdate, setLastOrderUpdate] = useState<OrderUpdateEvent["data"] | null>(null);
  const [lastRiskAlert, setLastRiskAlert] = useState<RiskAlertEvent["data"] | null>(null);
  const [lastRegimeChange, setLastRegimeChange] = useState<RegimeChangeEvent["data"] | null>(null);
  const [lastSchedulerEvent, setLastSchedulerEvent] = useState<SchedulerEventData["data"] | null>(
    null,
  );

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
      case "news_update":
        queryClient.invalidateQueries({ queryKey: ["news-articles"] });
        if (lastMessage.data.articles_fetched > 0) {
          toast(
            `${lastMessage.data.articles_fetched} new ${lastMessage.data.asset_class} articles`,
            "info",
          );
        }
        break;
      case "sentiment_update":
        queryClient.invalidateQueries({ queryKey: ["news-sentiment"] });
        queryClient.invalidateQueries({ queryKey: ["sentiment-signal"] });
        break;
      case "scheduler_event":
        setLastSchedulerEvent(lastMessage.data);
        queryClient.invalidateQueries({ queryKey: ["recent-jobs"] });
        queryClient.invalidateQueries({ queryKey: ["scheduler-tasks"] });
        if (lastMessage.data.status === "completed") {
          toast(`Task completed: ${lastMessage.data.task_name}`, "success");
        } else if (lastMessage.data.status === "failed") {
          toast(`Task failed: ${lastMessage.data.task_name}`, "error");
        }
        break;
      case "regime_change":
        setLastRegimeChange(lastMessage.data);
        queryClient.invalidateQueries({ queryKey: ["regime-overview"] });
        toast(
          `Regime change: ${lastMessage.data.symbol} ${lastMessage.data.previous_regime} → ${lastMessage.data.new_regime}`,
          "warning",
        );
        break;
    }
  }, [lastMessage, queryClient, toast]);

  return {
    isConnected,
    isHalted,
    haltReason,
    lastOrderUpdate,
    lastRiskAlert,
    lastRegimeChange,
    lastSchedulerEvent,
  };
}
