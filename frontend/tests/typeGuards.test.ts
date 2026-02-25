import { describe, expect, it } from "vitest";
import { isJobResult } from "../src/utils/typeGuards";

describe("isJobResult", () => {
  it("returns true for valid object with metrics", () => {
    expect(isJobResult({ metrics: { sharpe: 1.5 }, trades: [] })).toBe(true);
  });

  it("returns false for null", () => {
    expect(isJobResult(null)).toBe(false);
  });

  it("returns false for undefined", () => {
    expect(isJobResult(undefined)).toBe(false);
  });

  it("returns true for empty object", () => {
    expect(isJobResult({})).toBe(true);
  });
});
