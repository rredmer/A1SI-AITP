import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { SkeletonCard } from "../src/components/SkeletonCard";

describe("SkeletonCard", () => {
  it("renders with default height", () => {
    render(<SkeletonCard />);
    const card = screen.getByTestId("skeleton-card");
    expect(card).toBeInTheDocument();
    expect(card.className).toContain("h-24");
  });

  it("renders with custom height", () => {
    render(<SkeletonCard height="h-48" />);
    const card = screen.getByTestId("skeleton-card");
    expect(card.className).toContain("h-48");
  });
});
