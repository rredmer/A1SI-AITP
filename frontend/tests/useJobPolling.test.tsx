import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { ReactNode } from "react";
import { useJobPolling } from "../src/hooks/useJobPolling";

// Mock the jobs API
vi.mock("../src/api/jobs", () => ({
  jobsApi: {
    get: vi.fn(),
  },
}));

import { jobsApi } from "../src/api/jobs";
const mockGet = jobsApi.get as ReturnType<typeof vi.fn>;

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false, gcTime: 0 },
    },
  });
  return function Wrapper({ children }: { children: ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );
  };
}

describe("useJobPolling", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("does not fetch when jobId is null", () => {
    renderHook(() => useJobPolling(null), { wrapper: createWrapper() });
    expect(mockGet).not.toHaveBeenCalled();
  });

  it("fetches job when jobId is provided", async () => {
    mockGet.mockResolvedValue({
      id: "job-1",
      status: "completed",
      progress: 100,
    });

    const { result } = renderHook(() => useJobPolling("job-1"), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockGet).toHaveBeenCalledWith("job-1");
    expect(result.current.data?.status).toBe("completed");
  });

  it("returns job data with correct structure", async () => {
    const jobData = {
      id: "job-2",
      job_type: "backtest",
      status: "running" as const,
      progress: 50,
      progress_message: "Processing...",
      params: { strategy: "CryptoInvestorV1" },
      result: null,
      error: null,
      started_at: "2026-01-01T00:00:00Z",
      completed_at: null,
      created_at: "2026-01-01T00:00:00Z",
    };
    mockGet.mockResolvedValue(jobData);

    const { result } = renderHook(() => useJobPolling("job-2"), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data).toEqual(jobData);
  });

  it("has loading state while fetching", () => {
    mockGet.mockReturnValue(new Promise(() => {})); // never resolves

    const { result } = renderHook(() => useJobPolling("job-3"), {
      wrapper: createWrapper(),
    });

    expect(result.current.isLoading).toBe(true);
  });

  it("handles fetch error", async () => {
    mockGet.mockRejectedValue(new Error("Network error"));

    const { result } = renderHook(() => useJobPolling("job-4"), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });

    expect(result.current.error?.message).toBe("Network error");
  });
});
