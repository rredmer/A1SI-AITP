interface PaginationProps {
  page: number;
  pageSize: number;
  total: number;
  onPageChange: (page: number) => void;
}

/**
 * Simple prev/next pagination controls with page info.
 */
export function Pagination({ page, pageSize, total, onPageChange }: PaginationProps) {
  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  const start = (page - 1) * pageSize + 1;
  const end = Math.min(page * pageSize, total);

  if (total <= pageSize) return null;

  return (
    <div className="mt-3 flex items-center justify-between text-xs text-[var(--color-text-muted)]">
      <span>
        {start}–{end} of {total}
      </span>
      <div className="flex gap-1">
        <button
          onClick={() => onPageChange(page - 1)}
          disabled={page <= 1}
          className="rounded border border-[var(--color-border)] px-2 py-1 hover:bg-[var(--color-surface)] disabled:opacity-30"
        >
          Prev
        </button>
        <span className="px-2 py-1">
          {page} / {totalPages}
        </span>
        <button
          onClick={() => onPageChange(page + 1)}
          disabled={page >= totalPages}
          className="rounded border border-[var(--color-border)] px-2 py-1 hover:bg-[var(--color-surface)] disabled:opacity-30"
        >
          Next
        </button>
      </div>
    </div>
  );
}
