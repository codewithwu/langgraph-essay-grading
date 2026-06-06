import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, act } from "@testing-library/react";

const { streamMock, standardStream, gaokaoStream } = vi.hoisted(() => ({
  streamMock: vi.fn(),
  standardStream: vi.fn(),
  gaokaoStream: vi.fn(),
}));

vi.mock("../../src/workflow/graph", () => ({
  getGraph: (mode: string) => ({
    stream: (state: unknown) => {
      streamMock({ mode, state });
      return (async function* () {
        yield { check_relevance: { relevance: { score: 0.9, reason: "good" } } };
        yield { check_evidence: { evidence: { score: 0.7, reason: "ok" } } };
        yield { calculate_final_score: { final_score: 0.8 } };
      })();
    },
  }),
  standardGraph: { stream: standardStream },
  gaokaoGraph: { stream: gaokaoStream },
  graph: { stream: standardStream },
}));

import { useGradingStream } from "../../src/hooks/useGradingStream";

describe("useGradingStream", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("starts with empty events, not running, not done", () => {
    const { result } = renderHook(() => useGradingStream());
    expect(result.current.events).toEqual([]);
    expect(result.current.running).toBe(false);
    expect(result.current.done).toBe(false);
  });

  it("run() collects events and sets done=true", async () => {
    const { result } = renderHook(() => useGradingStream());

    await act(async () => {
      await result.current.run({ mode: "standard", topic: "t", essay: "e" });
    });

    expect(result.current.events.length).toBe(3);
    expect(result.current.events[0].node).toBe("check_relevance");
    expect(result.current.done).toBe(true);
    expect(result.current.running).toBe(false);
  });

  it("resets state between runs", async () => {
    const { result } = renderHook(() => useGradingStream());

    await act(async () => {
      await result.current.run({ mode: "standard", topic: "t", essay: "e" });
    });
    expect(result.current.events.length).toBe(3);

    await act(async () => {
      await result.current.run({ mode: "standard", topic: "t2", essay: "e2" });
    });
    expect(result.current.events.length).toBe(3);
  });
});
