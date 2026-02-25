interface FieldErrorProps {
  error?: string;
}

export function FieldError({ error }: FieldErrorProps) {
  if (!error) return null;
  return <p className="mt-1 text-xs text-[var(--color-danger)]">{error}</p>;
}
