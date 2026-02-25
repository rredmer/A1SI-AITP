import { ApiError } from "../api/client";

export function getErrorMessage(
  err: unknown,
  fallback = "An unexpected error occurred",
): string {
  if (err instanceof Error) return err.message;
  if (typeof err === "string") return err;
  return fallback;
}

export function getFieldErrors(err: unknown): Record<string, string> {
  if (err instanceof ApiError) return err.fieldErrors;
  return {};
}
