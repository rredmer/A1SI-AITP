interface SkeletonTableProps {
  rows?: number;
  cols?: number;
}

export function SkeletonTable({ rows = 5, cols = 4 }: SkeletonTableProps) {
  return (
    <div data-testid="skeleton-table" className="animate-pulse">
      {/* Header row */}
      <div className="mb-2 flex gap-4 border-b border-[var(--color-border)] pb-2">
        {Array.from({ length: cols }).map((_, c) => (
          <div key={c} className="h-3 flex-1 rounded bg-[var(--color-border)]" />
        ))}
      </div>
      {/* Data rows */}
      {Array.from({ length: rows }).map((_, r) => (
        <div key={r} className="mb-2 flex gap-4">
          {Array.from({ length: cols }).map((_, c) => (
            <div key={c} className="h-4 flex-1 rounded bg-[var(--color-border)]" />
          ))}
        </div>
      ))}
    </div>
  );
}
