import { describe, it, expect, vi } from "vitest";
import { screen, fireEvent } from "@testing-library/react";
import { ThemeToggle } from "../src/components/ThemeToggle";
import { renderWithProviders } from "./helpers";

// Mock useWebSocket to avoid real WebSocket connections
vi.mock("../src/hooks/useWebSocket", () => ({
  useWebSocket: () => ({ isConnected: false, lastMessage: null, send: vi.fn() }),
}));

describe("ThemeToggle", () => {
  it("renders theme toggle button", () => {
    renderWithProviders(<ThemeToggle />);
    expect(screen.getByRole("button", { name: /switch to light mode/i })).toBeInTheDocument();
  });

  it("shows Light Mode text in dark mode", () => {
    renderWithProviders(<ThemeToggle />);
    expect(screen.getByText("Light Mode")).toBeInTheDocument();
  });

  it("clicking toggles to light mode", () => {
    renderWithProviders(<ThemeToggle />);
    const btn = screen.getByRole("button", { name: /switch to light mode/i });
    fireEvent.click(btn);
    expect(screen.getByText("Dark Mode")).toBeInTheDocument();
  });

  it("clicking toggles back to dark mode", () => {
    renderWithProviders(<ThemeToggle />);
    const btn = screen.getByRole("button", { name: /switch to light mode/i });
    fireEvent.click(btn);
    expect(screen.getByText("Dark Mode")).toBeInTheDocument();
    const btn2 = screen.getByRole("button", { name: /switch to dark mode/i });
    fireEvent.click(btn2);
    expect(screen.getByText("Light Mode")).toBeInTheDocument();
  });

  it("default theme is dark", () => {
    renderWithProviders(<ThemeToggle />);
    expect(screen.getByText("Light Mode")).toBeInTheDocument();
  });
});
