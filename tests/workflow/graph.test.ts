import { describe, it, expect, vi, beforeEach } from "vitest";

vi.mock("../../src/workflow/llm", () => ({
  getLLM: () => ({
    withStructuredOutput: () => ({
      invoke: async () => ({ score: 0.8, reason: "mocked reason" }),
    }),
  }),
}));

import { graph } from "../../src/workflow/graph";

describe("graph integration", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("runs to completion and fills all 4 dimensions + final score", async () => {
    const result = await graph.invoke({
      topic: "我的梦想",
      essay: "我的梦想是当一名科学家...",
    });

    expect(result.relevance.score).toBe(0.8);
    expect(result.evidence.score).toBe(0.8);
    expect(result.structure.score).toBe(0.8);
    expect(result.expression.score).toBe(0.8);
    expect(result.final_score).toBe(0.8);
  });

  it("streams node updates in expected order", async () => {
    const seen: string[] = [];
    const stream = await graph.stream(
      { topic: "t", essay: "e" },
      { streamMode: "updates" },
    );
    for await (const event of stream) {
      for (const node of Object.keys(event)) {
        seen.push(node);
      }
    }

    expect(seen[0]).toBe("check_relevance");
    expect(seen).toContain("check_evidence");
    expect(seen).toContain("check_structure");
    expect(seen).toContain("check_expression");
    expect(seen[seen.length - 1]).toBe("calculate_final_score");
    expect(seen.length).toBeGreaterThanOrEqual(5);
  });
});
