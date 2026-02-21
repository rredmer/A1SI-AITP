import { describe, it, expect } from "vitest";
import { renderHook } from "@testing-library/react";
import type { ReactNode } from "react";
import { useToast } from "../src/hooks/useToast";
import { ToastProvider } from "../src/components/Toast";

describe("useToast", () => {
  it("throws when used outside ToastProvider", () => {
    // Suppress console.error from React for expected error
    const spy = vi.spyOn(console, "error").mockImplementation(() => {});

    expect(() => {
      renderHook(() => useToast());
    }).toThrow("useToast must be used within ToastProvider");

    spy.mockRestore();
  });

  it("returns toast function when inside ToastProvider", () => {
    function Wrapper({ children }: { children: ReactNode }) {
      return <ToastProvider>{children}</ToastProvider>;
    }

    const { result } = renderHook(() => useToast(), { wrapper: Wrapper });

    expect(result.current.toast).toBeDefined();
    expect(typeof result.current.toast).toBe("function");
  });
});
