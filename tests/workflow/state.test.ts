import { describe, it, expect } from "vitest";
import { ScoreDetail } from "../../src/workflow/state";

describe("ScoreDetail schema", () => {
  it("accepts valid input", () => {
    const r = ScoreDetail.safeParse({ score: 0.8, reason: "good" });
    expect(r.success).toBe(true);
  });

  it("rejects score < 0", () => {
    const r = ScoreDetail.safeParse({ score: -0.1, reason: "" });
    expect(r.success).toBe(false);
  });

  it("rejects score > 1", () => {
    const r = ScoreDetail.safeParse({ score: 1.1, reason: "" });
    expect(r.success).toBe(false);
  });

  it("rejects missing fields", () => {
    const r = ScoreDetail.safeParse({});
    expect(r.success).toBe(false);
  });
});
