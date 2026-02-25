/**
 * Type guard for job result data from background jobs.
 */
export function isJobResult(data: unknown): data is {
  metrics?: Record<string, unknown>;
  trades?: unknown[];
  strategies?: Record<string, Record<string, unknown>>;
  top_results?: Record<string, unknown>[];
} {
  return typeof data === "object" && data !== null;
}
