import { describe, it, expect, beforeEach, vi } from "vitest";
import { screen } from "@testing-library/react";
import { Routes, Route } from "react-router-dom";
import App from "../src/App";
import { Layout } from "../src/components/Layout";
import { renderWithProviders, mockFetch } from "./helpers";

beforeEach(() => {
  vi.stubGlobal("fetch", mockFetch({}));
});

describe("App", () => {
  it("renders the sidebar navigation", () => {
    renderWithProviders(<App />);
    expect(screen.getByText("CryptoInvestor")).toBeInTheDocument();
    const nav = screen.getByRole("navigation");
    expect(nav).toHaveTextContent("Dashboard");
    expect(nav).toHaveTextContent("Portfolio");
    expect(nav).toHaveTextContent("Market");
    expect(nav).toHaveTextContent("Trading");
    expect(nav).toHaveTextContent("Settings");
  });

  it("renders new nav items from Sprint 3 and 4", () => {
    renderWithProviders(<App />);
    const nav = screen.getByRole("navigation");
    expect(nav).toHaveTextContent("Regime");
    expect(nav).toHaveTextContent("Paper Trade");
  });

  it("renders all 11 navigation items", () => {
    renderWithProviders(<App />);
    const nav = screen.getByRole("navigation");
    const links = nav.querySelectorAll("a");
    expect(links.length).toBe(11);
  });
});

describe("Layout", () => {
  it("renders outlet content", () => {
    renderWithProviders(
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<div>Test Content</div>} />
        </Route>
      </Routes>,
    );
    expect(screen.getByText("Test Content")).toBeInTheDocument();
  });
});
