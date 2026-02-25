import { describe, it, expect } from "vitest";
import { screen } from "@testing-library/react";
import { FieldError } from "../src/components/FieldError";
import { renderWithProviders } from "./helpers";

describe("FieldError", () => {
  it("renders nothing when no error", () => {
    const { container } = renderWithProviders(<FieldError />);
    expect(container.querySelector("p")).toBeNull();
  });

  it("renders nothing when error is empty string", () => {
    const { container } = renderWithProviders(<FieldError error="" />);
    expect(container.querySelector("p")).toBeNull();
  });

  it("renders error message", () => {
    renderWithProviders(<FieldError error="Symbol is required" />);
    expect(screen.getByText("Symbol is required")).toBeInTheDocument();
  });
});
