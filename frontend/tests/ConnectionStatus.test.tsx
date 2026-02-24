import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { ConnectionStatus } from "../src/components/ConnectionStatus";

describe("ConnectionStatus", () => {
  it("renders connected state", () => {
    render(
      <ConnectionStatus
        isConnected={true}
        isReconnecting={false}
        reconnectAttempt={0}
        onReconnect={() => {}}
      />,
    );
    expect(screen.getByText("Connected")).toBeInTheDocument();
    expect(screen.getByLabelText("WebSocket connected")).toBeInTheDocument();
  });

  it("renders reconnecting with attempt count", () => {
    render(
      <ConnectionStatus
        isConnected={false}
        isReconnecting={true}
        reconnectAttempt={3}
        onReconnect={() => {}}
      />,
    );
    expect(screen.getByText("Reconnecting... (3)")).toBeInTheDocument();
    expect(screen.getByLabelText("WebSocket reconnecting")).toBeInTheDocument();
  });

  it("renders disconnected with reconnect button", () => {
    render(
      <ConnectionStatus
        isConnected={false}
        isReconnecting={false}
        reconnectAttempt={0}
        onReconnect={() => {}}
      />,
    );
    expect(screen.getByText("Disconnected")).toBeInTheDocument();
    expect(screen.getByText("Reconnect")).toBeInTheDocument();
  });

  it("reconnect button triggers callback", () => {
    const onReconnect = vi.fn();
    render(
      <ConnectionStatus
        isConnected={false}
        isReconnecting={false}
        reconnectAttempt={0}
        onReconnect={onReconnect}
      />,
    );
    fireEvent.click(screen.getByText("Reconnect"));
    expect(onReconnect).toHaveBeenCalledOnce();
  });

  it("has accessibility attributes", () => {
    render(
      <ConnectionStatus
        isConnected={true}
        isReconnecting={false}
        reconnectAttempt={0}
        onReconnect={() => {}}
      />,
    );
    const status = screen.getByRole("status");
    expect(status).toHaveAttribute("aria-live", "polite");
  });

  it("reconnecting state shows amber indicator", () => {
    render(
      <ConnectionStatus
        isConnected={false}
        isReconnecting={true}
        reconnectAttempt={1}
        onReconnect={() => {}}
      />,
    );
    const indicator = screen.getByLabelText("WebSocket reconnecting");
    expect(indicator.className).toContain("bg-amber-400");
    expect(indicator.className).toContain("animate-pulse");
  });
});
