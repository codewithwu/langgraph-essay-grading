import { describe, it, expect, beforeEach, vi } from "vitest";
import { loadMode, saveMode, DEFAULT_MODE } from "../../src/lib/mode-storage";

describe("mode-storage", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.restoreAllMocks();
  });

  it("默认值为 gaokao", () => {
    expect(DEFAULT_MODE).toBe("gaokao");
    expect(loadMode()).toBe("gaokao");
  });

  it("save 后 load 读出相同值", () => {
    saveMode("standard");
    expect(loadMode()).toBe("standard");
  });

  it("非法值回退为 gaokao 并 warn", () => {
    const warn = vi.spyOn(console, "warn").mockImplementation(() => {});
    localStorage.setItem("grading-mode-v1", JSON.stringify("foo"));
    expect(loadMode()).toBe("gaokao");
    expect(warn).toHaveBeenCalled();
  });

  it("localStorage 抛错时 load 不抛", () => {
    const getItem = vi.spyOn(Storage.prototype, "getItem").mockImplementation(() => {
      throw new Error("quota");
    });
    expect(() => loadMode()).not.toThrow();
    expect(loadMode()).toBe("gaokao");
    getItem.mockRestore();
  });

  it("localStorage 抛错时 save 静默失败", () => {
    const setItem = vi.spyOn(Storage.prototype, "setItem").mockImplementation(() => {
      throw new Error("quota");
    });
    expect(() => saveMode("standard")).not.toThrow();
    setItem.mockRestore();
  });
});
