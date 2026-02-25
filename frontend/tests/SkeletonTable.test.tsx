import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { SkeletonTable } from "../src/components/SkeletonTable";

describe("SkeletonTable", () => {
  it("renders correct rows and cols", () => {
    render(<SkeletonTable rows={3} cols={2} />);
    const table = screen.getByTestId("skeleton-table");
    expect(table).toBeInTheDocument();
    // 1 header row + 3 data rows = 4 flex rows
    const rows = table.querySelectorAll(":scope > div");
    expect(rows.length).toBe(4); // 1 header + 3 data
  });

  it("renders default 5 rows and 4 cols", () => {
    render(<SkeletonTable />);
    const table = screen.getByTestId("skeleton-table");
    const rows = table.querySelectorAll(":scope > div");
    expect(rows.length).toBe(6); // 1 header + 5 data
  });
});
