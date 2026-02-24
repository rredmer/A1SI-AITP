import { createContext } from "react";

export interface ToastContextValue {
  toast: (message: string, type?: "success" | "error" | "info" | "warning") => void;
}

export const ToastContext = createContext<ToastContextValue | null>(null);
