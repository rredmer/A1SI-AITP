import { describe, expect, it } from "vitest";
import { getErrorMessage } from "../src/utils/errors";

describe("getErrorMessage", () => {
  it("returns message from Error instance", () => {
    expect(getErrorMessage(new Error("test error"))).toBe("test error");
  });

  it("returns string error directly", () => {
    expect(getErrorMessage("string error")).toBe("string error");
  });

  it("returns fallback for null", () => {
    expect(getErrorMessage(null)).toBe("An unexpected error occurred");
  });

  it("returns fallback for undefined", () => {
    expect(getErrorMessage(undefined)).toBe("An unexpected error occurred");
  });

  it("returns fallback for plain object", () => {
    expect(getErrorMessage({ code: 500 })).toBe("An unexpected error occurred");
  });

  it("returns custom fallback", () => {
    expect(getErrorMessage(42, "Custom fallback")).toBe("Custom fallback");
  });

  it("getFieldErrors returns field errors from ApiError", async () => {
    const { getFieldErrors } = await import("../src/utils/errors");
    const { ApiError } = await import("../src/api/client");
    const err = new ApiError(400, "Bad Request", { symbol: ["Too short"], amount: ["Required"] });
    const fields = getFieldErrors(err);
    expect(fields.symbol).toBe("Too short");
    expect(fields.amount).toBe("Required");
  });

  it("getFieldErrors returns empty object for non-ApiError", async () => {
    const { getFieldErrors } = await import("../src/utils/errors");
    const fields = getFieldErrors(new Error("generic error"));
    expect(fields).toEqual({});
  });
});
