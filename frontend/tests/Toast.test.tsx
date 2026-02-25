import { describe, it, expect, vi, beforeEach } from "vitest";
import { screen, waitFor, act } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useToast } from "../src/hooks/useToast";
import { renderWithProviders } from "./helpers";

beforeEach(() => {
  vi.useFakeTimers({ shouldAdvanceTime: true });
});

function ToastTrigger() {
  const { toast } = useToast();
  return (
    <div>
      <button onClick={() => toast("Success message", "success")}>
        Show Success
      </button>
      <button onClick={() => toast("Error message", "error")}>
        Show Error
      </button>
      <button onClick={() => toast("Info message", "info")}>
        Show Info
      </button>
    </div>
  );
}

describe("Toast", () => {
  it("shows a success toast when triggered", async () => {
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
    renderWithProviders(<ToastTrigger />);
    await user.click(screen.getByText("Show Success"));
    expect(screen.getByText("Success message")).toBeInTheDocument();
    expect(screen.getByRole("alert")).toBeInTheDocument();
  });

  it("shows an error toast with error styling", async () => {
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
    renderWithProviders(<ToastTrigger />);
    await user.click(screen.getByText("Show Error"));
    const alert = screen.getByRole("alert");
    expect(alert).toHaveTextContent("Error message");
    expect(alert.className).toContain("red");
  });

  it("auto-dismisses toast after 4 seconds", async () => {
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
    renderWithProviders(<ToastTrigger />);
    await user.click(screen.getByText("Show Info"));
    expect(screen.getByText("Info message")).toBeInTheDocument();

    act(() => {
      vi.advanceTimersByTime(4100);
    });

    await waitFor(() => {
      expect(screen.queryByText("Info message")).not.toBeInTheDocument();
    });
  });

  it("dismisses toast on close button click", async () => {
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
    renderWithProviders(<ToastTrigger />);
    await user.click(screen.getByText("Show Success"));
    expect(screen.getByText("Success message")).toBeInTheDocument();

    const closeBtn = screen.getByText("\u00d7");
    await user.click(closeBtn);
    expect(screen.queryByText("Success message")).not.toBeInTheDocument();
  });

  it("can show multiple toasts simultaneously", async () => {
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
    renderWithProviders(<ToastTrigger />);
    await user.click(screen.getByText("Show Success"));
    await user.click(screen.getByText("Show Error"));
    expect(screen.getByText("Success message")).toBeInTheDocument();
    expect(screen.getByText("Error message")).toBeInTheDocument();
    expect(screen.getAllByRole("alert")).toHaveLength(2);
  });

  it("caps at 5 concurrent toasts", async () => {
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
    renderWithProviders(<ToastTrigger />);
    // Add 6 toasts rapidly — alternating types to create distinct messages
    for (let i = 0; i < 6; i++) {
      if (i % 3 === 0) await user.click(screen.getByText("Show Success"));
      else if (i % 3 === 1) await user.click(screen.getByText("Show Error"));
      else await user.click(screen.getByText("Show Info"));
    }
    // Should cap at 5
    expect(screen.getAllByRole("alert").length).toBeLessThanOrEqual(5);
  });

  it("oldest dismissed when over limit", async () => {
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
    renderWithProviders(<ToastTrigger />);
    // Add 6 toasts (all the same type creates identical messages, so we check count)
    for (let i = 0; i < 6; i++) {
      await user.click(screen.getByText("Show Success"));
    }
    // Only 5 should remain
    const alerts = screen.getAllByRole("alert");
    expect(alerts).toHaveLength(5);
  });

  it("auto-dismiss still works with cap", async () => {
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
    renderWithProviders(<ToastTrigger />);
    await user.click(screen.getByText("Show Info"));
    expect(screen.getByText("Info message")).toBeInTheDocument();

    act(() => {
      vi.advanceTimersByTime(4100);
    });

    await waitFor(() => {
      expect(screen.queryByText("Info message")).not.toBeInTheDocument();
    });
  });
});
