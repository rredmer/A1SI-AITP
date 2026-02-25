export class ApiError extends Error {
  status: number;
  body: unknown;

  constructor(status: number, statusText: string, body: unknown) {
    const msg =
      typeof body === "object" && body !== null && "error" in body
        ? String((body as Record<string, unknown>).error)
        : `API error: ${status} ${statusText}`;
    super(msg);
    this.name = "ApiError";
    this.status = status;
    this.body = body;
  }

  get fieldErrors(): Record<string, string> {
    if (!this.body || typeof this.body !== "object") return {};
    const result: Record<string, string> = {};
    for (const [key, val] of Object.entries(
      this.body as Record<string, unknown>,
    )) {
      if (key === "error" || key === "detail" || key === "status_code")
        continue;
      if (Array.isArray(val) && val.length > 0) result[key] = String(val[0]);
      else if (typeof val === "string") result[key] = val;
    }
    return result;
  }
}

const BASE_URL = "/api";

function getCsrfToken(): string {
  const match = document.cookie
    .split("; ")
    .find((row) => row.startsWith("csrftoken="));
  return match ? match.split("=")[1] : "";
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const method = options?.method ?? "GET";
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };

  // Add CSRF token for state-changing requests
  if (["POST", "PUT", "DELETE", "PATCH"].includes(method)) {
    headers["X-CSRFToken"] = getCsrfToken();
  }

  const response = await fetch(`${BASE_URL}${path}`, {
    credentials: "include",
    headers,
    ...options,
    // Ensure our headers aren't overwritten by spread
  });

  if (response.status === 401) {
    // Redirect to login on auth failure (unless already on login page)
    if (!window.location.pathname.startsWith("/login")) {
      window.location.href = "/login";
    }
    throw new Error("Unauthorized");
  }

  if (response.status === 403) {
    // Possibly a CSRF error — retry once with fresh token
    const body = await response.text();
    if (body.includes("CSRF")) {
      throw new Error("CSRF validation failed. Please refresh and try again.");
    }
    throw new Error(`Forbidden: ${response.statusText}`);
  }

  if (!response.ok) {
    let body: unknown = null;
    try {
      body = await response.json();
    } catch {
      /* not JSON */
    }
    throw new ApiError(response.status, response.statusText, body);
  }
  if (response.status === 204) return undefined as T;
  return response.json();
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body?: unknown) =>
    request<T>(path, {
      method: "POST",
      body: body ? JSON.stringify(body) : undefined,
    }),
  put: <T>(path: string, body: unknown) =>
    request<T>(path, { method: "PUT", body: JSON.stringify(body) }),
  patch: <T>(path: string, body: unknown) =>
    request<T>(path, { method: "PATCH", body: JSON.stringify(body) }),
  delete: <T>(path: string) => request<T>(path, { method: "DELETE" }),
};
