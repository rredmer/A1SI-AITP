interface ProgressBarProps {
  progress: number; // 0 to 1
  message?: string;
  className?: string;
}

export function ProgressBar({ progress, message, className = "" }: ProgressBarProps) {
  const pct = Math.round(progress * 100);
  return (
    <div className={className}>
      <div className="flex items-center justify-between text-xs text-[var(--color-text-muted)] mb-1">
        <span>{message || "Processing..."}</span>
        <span>{pct}%</span>
      </div>
      <div className="h-2 w-full overflow-hidden rounded-full bg-[var(--color-bg)]">
        <div
          className="h-full rounded-full bg-[var(--color-primary)] transition-all duration-300"
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}
