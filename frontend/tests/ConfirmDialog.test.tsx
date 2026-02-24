import { describe, it, expect, vi } from "vitest";
import { screen, fireEvent } from "@testing-library/react";
import { ConfirmDialog } from "../src/components/ConfirmDialog";
import { renderWithProviders } from "./helpers";

const defaultProps = {
  open: true,
  title: "Confirm Action",
  message: "Are you sure you want to proceed?",
  onConfirm: vi.fn(),
  onCancel: vi.fn(),
};

describe("ConfirmDialog", () => {
  it("renders when open", () => {
    renderWithProviders(<ConfirmDialog {...defaultProps} />);
    expect(screen.getByText("Confirm Action")).toBeInTheDocument();
    expect(screen.getByText("Are you sure you want to proceed?")).toBeInTheDocument();
  });

  it("is hidden when closed", () => {
    renderWithProviders(<ConfirmDialog {...defaultProps} open={false} />);
    expect(screen.queryByText("Confirm Action")).not.toBeInTheDocument();
  });

  it("displays title and message", () => {
    renderWithProviders(
      <ConfirmDialog {...defaultProps} title="Delete Item" message="This will delete the item." />,
    );
    expect(screen.getByText("Delete Item")).toBeInTheDocument();
    expect(screen.getByText("This will delete the item.")).toBeInTheDocument();
  });

  it("uses custom labels", () => {
    renderWithProviders(
      <ConfirmDialog {...defaultProps} confirmLabel="Yes, Delete" cancelLabel="No, Keep" />,
    );
    expect(screen.getByText("Yes, Delete")).toBeInTheDocument();
    expect(screen.getByText("No, Keep")).toBeInTheDocument();
  });

  it("calls onConfirm when confirm button is clicked", () => {
    const onConfirm = vi.fn();
    renderWithProviders(<ConfirmDialog {...defaultProps} onConfirm={onConfirm} />);
    fireEvent.click(screen.getByText("Confirm"));
    expect(onConfirm).toHaveBeenCalledOnce();
  });

  it("calls onCancel when cancel button is clicked", () => {
    const onCancel = vi.fn();
    renderWithProviders(<ConfirmDialog {...defaultProps} onCancel={onCancel} />);
    fireEvent.click(screen.getByText("Cancel"));
    expect(onCancel).toHaveBeenCalledOnce();
  });

  it("disables buttons when isPending", () => {
    renderWithProviders(<ConfirmDialog {...defaultProps} isPending={true} />);
    expect(screen.getByText("Processing...")).toBeInTheDocument();
    const buttons = screen.getAllByRole("button");
    buttons.forEach((btn) => expect(btn).toBeDisabled());
  });

  it("applies danger variant styling", () => {
    renderWithProviders(<ConfirmDialog {...defaultProps} variant="danger" />);
    const confirmBtn = screen.getByText("Confirm");
    expect(confirmBtn.className).toContain("bg-red-600");
  });

  it("closes on Escape key", () => {
    const onCancel = vi.fn();
    renderWithProviders(<ConfirmDialog {...defaultProps} onCancel={onCancel} />);
    fireEvent.keyDown(document, { key: "Escape" });
    expect(onCancel).toHaveBeenCalledOnce();
  });

  it("has correct aria attributes", () => {
    renderWithProviders(<ConfirmDialog {...defaultProps} />);
    const dialog = screen.getByRole("dialog");
    expect(dialog).toHaveAttribute("aria-modal", "true");
    expect(dialog).toHaveAttribute("aria-labelledby", "confirm-dialog-title");
  });
});
