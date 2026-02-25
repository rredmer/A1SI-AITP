interface SkeletonCardProps {
  height?: string;
}

export function SkeletonCard({ height = "h-24" }: SkeletonCardProps) {
  return (
    <div
      data-testid="skeleton-card"
      className={`animate-pulse rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] ${height}`}
    >
      <div className="p-4">
        <div className="mb-2 h-3 w-1/3 rounded bg-[var(--color-border)]" />
        <div className="h-6 w-2/3 rounded bg-[var(--color-border)]" />
      </div>
    </div>
  );
}
