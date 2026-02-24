import { describe, it, expect, beforeEach, vi } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import { Settings } from "../src/pages/Settings";
import { renderWithProviders, mockFetch } from "./helpers";

const auditData = {
  results: [
    {
      id: 1,
      user: "admin",
      action: "GET /api/health/",
      ip_address: "127.0.0.1",
      status_code: 200,
      created_at: "2026-02-24T12:00:00Z",
    },
    {
      id: 2,
      user: "trader",
      action: "POST /api/trading/orders/",
      ip_address: "192.168.1.1",
      status_code: 201,
      created_at: "2026-02-24T12:05:00Z",
    },
  ],
  total: 2,
};

const handlers = {
  "/api/exchange-configs/": [],
  "/api/data-sources/": [],
  "/api/audit-log/": auditData,
  "/api/notifications/": {},
  "/api/portfolios/": [{ id: 1, name: "Main" }],
};

beforeEach(() => {
  vi.stubGlobal("fetch", mockFetch(handlers));
});

describe("AuditLog Section in Settings", () => {
  it("renders the audit log table", async () => {
    renderWithProviders(<Settings />);
    await waitFor(() => {
      expect(screen.getByText("Audit Log")).toBeInTheDocument();
    });
  });

  it("renders audit entries when data exists", async () => {
    renderWithProviders(<Settings />);
    await waitFor(() => {
      expect(screen.getByText("GET /api/health/")).toBeInTheDocument();
    });
    expect(screen.getByText("admin")).toBeInTheDocument();
    expect(screen.getByText("127.0.0.1")).toBeInTheDocument();
  });

  it("renders filter inputs", async () => {
    renderWithProviders(<Settings />);
    await waitFor(() => {
      expect(screen.getByPlaceholderText("Filter by user")).toBeInTheDocument();
    });
  });

  it("shows empty state when no data", async () => {
    vi.stubGlobal(
      "fetch",
      mockFetch({
        ...handlers,
        "/api/audit-log/": { results: [], total: 0 },
      }),
    );
    renderWithProviders(<Settings />);
    await waitFor(() => {
      expect(screen.getByText("No audit log entries found.")).toBeInTheDocument();
    });
  });
});
