import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { renderHook, act, waitFor } from "@testing-library/react";
import { useAuth } from "../src/hooks/useAuth";

describe("useAuth", () => {
  const originalFetch = globalThis.fetch;

  beforeEach(() => {
    Object.defineProperty(document, "cookie", {
      writable: true,
      value: "csrftoken=test-token",
    });
  });

  afterEach(() => {
    globalThis.fetch = originalFetch;
  });

  function mockAuthFetch(
    responses: Record<string, { ok: boolean; data: unknown }>,
  ) {
    globalThis.fetch = vi.fn((input: RequestInfo | URL) => {
      const url = typeof input === "string" ? input : input.toString();
      for (const [pattern, resp] of Object.entries(responses)) {
        if (url.includes(pattern)) {
          return Promise.resolve({
            ok: resp.ok,
            status: resp.ok ? 200 : 401,
            json: () => Promise.resolve(resp.data),
          } as Response);
        }
      }
      return Promise.resolve({
        ok: false,
        status: 404,
        json: () => Promise.resolve({}),
      } as Response);
    });
  }

  it("starts in loading state", () => {
    mockAuthFetch({
      "/api/auth/status/": {
        ok: true,
        data: { authenticated: true, username: "admin" },
      },
    });

    const { result } = renderHook(() => useAuth());
    expect(result.current.isLoading).toBe(true);
    expect(result.current.isAuthenticated).toBe(false);
  });

  it("sets authenticated after successful status check", async () => {
    mockAuthFetch({
      "/api/auth/status/": {
        ok: true,
        data: { authenticated: true, username: "admin" },
      },
    });

    const { result } = renderHook(() => useAuth());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });
    expect(result.current.isAuthenticated).toBe(true);
    expect(result.current.username).toBe("admin");
  });

  it("sets unauthenticated when status check returns false", async () => {
    mockAuthFetch({
      "/api/auth/status/": {
        ok: true,
        data: { authenticated: false },
      },
    });

    const { result } = renderHook(() => useAuth());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });
    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.username).toBeNull();
  });

  it("handles failed status check gracefully", async () => {
    mockAuthFetch({
      "/api/auth/status/": { ok: false, data: {} },
    });

    const { result } = renderHook(() => useAuth());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });
    expect(result.current.isAuthenticated).toBe(false);
  });

  it("handles network error gracefully", async () => {
    globalThis.fetch = vi.fn().mockRejectedValue(new Error("Network error"));

    const { result } = renderHook(() => useAuth());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });
    expect(result.current.isAuthenticated).toBe(false);
  });

  it("login() returns null on success and updates state", async () => {
    mockAuthFetch({
      "/api/auth/status/": {
        ok: true,
        data: { authenticated: false },
      },
      "/api/auth/login/": {
        ok: true,
        data: { username: "admin" },
      },
    });

    const { result } = renderHook(() => useAuth());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    let error: string | null = "initial";
    await act(async () => {
      error = await result.current.login("admin", "admin");
    });

    expect(error).toBeNull();
    expect(result.current.isAuthenticated).toBe(true);
    expect(result.current.username).toBe("admin");
  });

  it("login() returns error message on failure", async () => {
    mockAuthFetch({
      "/api/auth/status/": {
        ok: true,
        data: { authenticated: false },
      },
      "/api/auth/login/": {
        ok: false,
        data: { error: "Invalid credentials" },
      },
    });

    const { result } = renderHook(() => useAuth());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    let error: string | null = null;
    await act(async () => {
      error = await result.current.login("admin", "wrong");
    });

    expect(error).toBe("Invalid credentials");
    expect(result.current.isAuthenticated).toBe(false);
  });

  it("login() returns default error when no error field", async () => {
    mockAuthFetch({
      "/api/auth/status/": {
        ok: true,
        data: { authenticated: false },
      },
      "/api/auth/login/": {
        ok: false,
        data: {},
      },
    });

    const { result } = renderHook(() => useAuth());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    let error: string | null = null;
    await act(async () => {
      error = await result.current.login("admin", "wrong");
    });

    expect(error).toBe("Login failed");
  });

  it("logout() clears auth state", async () => {
    mockAuthFetch({
      "/api/auth/status/": {
        ok: true,
        data: { authenticated: true, username: "admin" },
      },
      "/api/auth/logout/": { ok: true, data: {} },
    });

    const { result } = renderHook(() => useAuth());

    await waitFor(() => {
      expect(result.current.isAuthenticated).toBe(true);
    });

    await act(async () => {
      await result.current.logout();
    });

    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.username).toBeNull();
  });

  it("login sends CSRF token in header", async () => {
    mockAuthFetch({
      "/api/auth/status/": {
        ok: true,
        data: { authenticated: false },
      },
      "/api/auth/login/": {
        ok: true,
        data: { username: "admin" },
      },
    });

    const { result } = renderHook(() => useAuth());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    await act(async () => {
      await result.current.login("admin", "admin");
    });

    const fetchMock = globalThis.fetch as ReturnType<typeof vi.fn>;
    const loginCall = fetchMock.mock.calls.find(
      (c: [string, RequestInit]) =>
        typeof c[0] === "string" && c[0].includes("/login/"),
    );
    expect(loginCall).toBeDefined();
    expect(loginCall[1].headers["X-CSRFToken"]).toBe("test-token");
  });

  it("checkAuth can be called manually", async () => {
    let callCount = 0;
    globalThis.fetch = vi.fn(() => {
      callCount++;
      return Promise.resolve({
        ok: true,
        status: 200,
        json: () =>
          Promise.resolve({
            authenticated: callCount > 1,
            username: callCount > 1 ? "admin" : null,
          }),
      } as Response);
    });

    const { result } = renderHook(() => useAuth());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });
    expect(result.current.isAuthenticated).toBe(false);

    await act(async () => {
      await result.current.checkAuth();
    });

    expect(result.current.isAuthenticated).toBe(true);
  });
});
