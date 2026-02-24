interface ConnectionStatusProps {
  isConnected: boolean;
  isReconnecting: boolean;
  reconnectAttempt: number;
  onReconnect: () => void;
}

export function ConnectionStatus({
  isConnected,
  isReconnecting,
  reconnectAttempt,
  onReconnect,
}: ConnectionStatusProps) {
  if (isConnected) {
    return (
      <div className="flex items-center gap-2 px-3" aria-live="polite" role="status">
        <span
          aria-label="WebSocket connected"
          className="h-2 w-2 rounded-full bg-green-400"
        />
        <span className="text-xs text-[var(--color-text-muted)]">Connected</span>
      </div>
    );
  }

  if (isReconnecting) {
    return (
      <div className="flex items-center gap-2 px-3" aria-live="polite" role="status">
        <span
          aria-label="WebSocket reconnecting"
          className="h-2 w-2 animate-pulse rounded-full bg-amber-400"
        />
        <span className="text-xs text-amber-400">
          Reconnecting... ({reconnectAttempt})
        </span>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-2 px-3" aria-live="polite" role="status">
      <span
        aria-label="WebSocket disconnected"
        className="h-2 w-2 rounded-full bg-red-400"
      />
      <span className="text-xs text-red-400">Disconnected</span>
      <button
        onClick={onReconnect}
        className="rounded border border-red-700 px-1.5 py-0.5 text-xs text-red-400 hover:bg-red-900/30"
      >
        Reconnect
      </button>
    </div>
  );
}
