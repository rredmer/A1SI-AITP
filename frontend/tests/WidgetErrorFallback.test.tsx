import { describe, it, expect, vi, beforeEach } from "vitest";
import { screen } from "@testing-library/react";
import { ErrorBoundary } from "../src/components/ErrorBoundary";
import { WidgetErrorFallback } from "../src/components/WidgetErrorFallback";
import { renderWithProviders } from "./helpers";

beforeEach(() => {
  vi.spyOn(console, "error").mockImplementation(() => {});
});

function ThrowingWidget() {
  throw new Error("Widget crash");
}

describe("WidgetErrorFallback", () => {
  it("renders widget name", () => {
    renderWithProviders(<WidgetErrorFallback name="Price Chart" />);
    expect(screen.getByText("Price Chart unavailable")).toBeInTheDocument();
  });

  it("renders role alert", () => {
    renderWithProviders(<WidgetErrorFallback name="Price Chart" />);
    expect(screen.getByRole("alert")).toBeInTheDocument();
  });

  it("compact variant has h-24 class", () => {
    renderWithProviders(<WidgetErrorFallback name="Price Chart" compact />);
    const el = screen.getByRole("alert");
    expect(el.className).toContain("h-24");
  });

  it("default height has h-48 class", () => {
    renderWithProviders(<WidgetErrorFallback name="Price Chart" />);
    const el = screen.getByRole("alert");
    expect(el.className).toContain("h-48");
  });

  it("error boundary uses fallback instead of default", () => {
    renderWithProviders(
      <ErrorBoundary fallback={<WidgetErrorFallback name="Price Chart" />}>
        <ThrowingWidget />
      </ErrorBoundary>,
    );
    expect(screen.getByText("Price Chart unavailable")).toBeInTheDocument();
    expect(screen.queryByText("Something went wrong")).not.toBeInTheDocument();
  });

  it("supports different widget names", () => {
    renderWithProviders(<WidgetErrorFallback name="Equity Curve" />);
    expect(screen.getByText("Equity Curve unavailable")).toBeInTheDocument();
  });
});
