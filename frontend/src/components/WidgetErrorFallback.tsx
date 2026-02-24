interface WidgetErrorFallbackProps {
  name: string;
  compact?: boolean;
}

export function WidgetErrorFallback({ name, compact = false }: WidgetErrorFallbackProps) {
  return (
    <div
      role="alert"
      className={`flex items-center justify-center rounded-xl border border-red-500/20 bg-red-500/5 ${compact ? "h-24" : "h-48"}`}
    >
      <p className="text-sm text-red-400">{name} unavailable</p>
    </div>
  );
}
