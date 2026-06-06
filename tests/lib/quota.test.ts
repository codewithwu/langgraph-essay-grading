import { describe, it, expect, beforeEach, vi } from "vitest";
import { loadQuota, saveQuota, incrementQuota, QUOTA_LIMIT, type QuotaState } from "../../src/lib/quota";

describe("quota", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.restoreAllMocks();
  });

  describe("loadQuota", () => {
    it("returns { used: 0 } when storage is empty", () => {
      expect(loadQuota()).toEqual({ used: 0 });
    });

    it("returns { used: 0 } when JSON is corrupt", () => {
      localStorage.setItem("grading-quota-v1", "{not valid");
      expect(loadQuota()).toEqual({ used: 0 });
    });

    it("parses normal { used: 3 }", () => {
      localStorage.setItem("grading-quota-v1", JSON.stringify({ used: 3 }));
      expect(loadQuota()).toEqual({ used: 3 });
    });

    it("corrects negative used to 0", () => {
      localStorage.setItem("grading-quota-v1", JSON.stringify({ used: -1 }));
      expect(loadQuota()).toEqual({ used: 0 });
    });

    it("clamps used above QUOTA_LIMIT to QUOTA_LIMIT", () => {
      localStorage.setItem("grading-quota-v1", JSON.stringify({ used: 15 }));
      expect(loadQuota().used).toBe(QUOTA_LIMIT);
    });

    it("floors fractional used", () => {
      localStorage.setItem("grading-quota-v1", JSON.stringify({ used: 3.7 }));
      expect(loadQuota()).toEqual({ used: 3 });
    });

    it("corrects non-numeric used to 0", () => {
      localStorage.setItem("grading-quota-v1", JSON.stringify({ used: "abc" }));
      expect(loadQuota()).toEqual({ used: 0 });
    });
  });

  describe("saveQuota + loadQuota round-trip", () => {
    it("round-trips through save and load", () => {
      const s: QuotaState = { used: 5 };
      saveQuota(s);
      expect(loadQuota()).toEqual(s);
    });
  });

  describe("incrementQuota", () => {
    it("increments from 0 to 1", () => {
      const result = incrementQuota();
      expect(result).toEqual({ used: 1 });
      expect(loadQuota()).toEqual({ used: 1 });
    });

    it("increments from 9 to QUOTA_LIMIT", () => {
      saveQuota({ used: 9 });
      expect(incrementQuota()).toEqual({ used: QUOTA_LIMIT });
    });

    it("does not exceed QUOTA_LIMIT when already at limit", () => {
      saveQuota({ used: QUOTA_LIMIT });
      expect(incrementQuota()).toEqual({ used: QUOTA_LIMIT });
    });

    it("does not increment when storage write fails", () => {
      saveQuota({ used: 3 });
      const spy = vi.spyOn(Storage.prototype, "setItem").mockImplementation(() => {
        throw new Error("quota exceeded");
      });
      const warn = vi.spyOn(console, "warn").mockImplementation(() => {});
      const result = incrementQuota();
      expect(result).toEqual({ used: 3 });
      expect(warn).toHaveBeenCalled();
      spy.mockRestore();
    });
  });
});
