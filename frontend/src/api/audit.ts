import { api } from "./client";
import type { AuditLogResponse } from "../types";

export interface AuditLogParams {
  user?: string;
  action?: string;
  status_code?: number;
  created_after?: string;
  created_before?: string;
  limit?: number;
  offset?: number;
}

export const auditApi = {
  list: (params?: AuditLogParams) => {
    const query = new URLSearchParams();
    if (params?.user) query.set("user", params.user);
    if (params?.action) query.set("action", params.action);
    if (params?.status_code != null) query.set("status_code", String(params.status_code));
    if (params?.created_after) query.set("created_after", params.created_after);
    if (params?.created_before) query.set("created_before", params.created_before);
    if (params?.limit != null) query.set("limit", String(params.limit));
    if (params?.offset != null) query.set("offset", String(params.offset));
    const qs = query.toString();
    return api.get<AuditLogResponse>(`/audit-log/${qs ? `?${qs}` : ""}`);
  },
};
