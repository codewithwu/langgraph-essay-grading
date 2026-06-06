import { describe, it, expect, beforeEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useQuota, QUOTA_LIMIT } from "../../src/hooks/useQuota";

describe("useQuota", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it("starts with used: 0, remaining: QUOTA_LIMIT, exhausted: false", () => {
    const { result } = renderHook(() => useQuota());
    expect(result.current.used).toBe(0);
    expect(result.current.remaining).toBe(QUOTA_LIMIT);
    expect(result.current.exhausted).toBe(false);
  });

  it("increment() increases used by 1", () => {
    const { result } = renderHook(() => useQuota());
    act(() => result.current.increment());
    expect(result.current.used).toBe(1);
    expect(result.current.remaining).toBe(QUOTA_LIMIT - 1);
  });

  it("increment() persists to localStorage", () => {
    const { result } = renderHook(() => useQuota());
    act(() => result.current.increment());
    expect(JSON.parse(localStorage.getItem("grading-quota-v1") ?? "{}")).toEqual({ used: 1 });
  });

  it("exhausted becomes true when used === QUOTA_LIMIT", () => {
    localStorage.setItem("grading-quota-v1", JSON.stringify({ used: QUOTA_LIMIT }));
    const { result } = renderHook(() => useQuota());
    expect(result.current.used).toBe(QUOTA_LIMIT);
    expect(result.current.remaining).toBe(0);
    expect(result.current.exhausted).toBe(true);
  });

  it("multiple increments accumulate", () => {
    const { result } = renderHook(() => useQuota());
    act(() => {
      result.current.increment();
      result.current.increment();
      result.current.increment();
    });
    expect(result.current.used).toBe(3);
    expect(result.current.exhausted).toBe(false);
  });
});
