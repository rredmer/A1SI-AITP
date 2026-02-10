import { api } from "./client";
import type { PlatformStatus } from "../types";

export const platformApi = {
  status: () => api.get<PlatformStatus>("/platform/status"),
  config: () => api.get<Record<string, unknown>>("/platform/config"),
};
