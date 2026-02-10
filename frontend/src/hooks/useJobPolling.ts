import { useQuery } from "@tanstack/react-query";
import { jobsApi } from "../api/jobs";
import type { BackgroundJob } from "../types";

/**
 * Poll a background job by ID every 2s while it's pending/running.
 * Stops polling once the job completes, fails, or is cancelled.
 */
export function useJobPolling(jobId: string | null) {
  return useQuery<BackgroundJob>({
    queryKey: ["job", jobId],
    queryFn: () => jobsApi.get(jobId!),
    enabled: !!jobId,
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      if (status === "pending" || status === "running") return 2000;
      return false;
    },
  });
}
