import { describe, it, expect } from "vitest";
import { routeRelevance } from "../../src/workflow/routes";
import type { EssayStateType } from "../../src/workflow/state";

const mkState = (score: number): EssayStateType =>
  ({
    topic: "t",
    essay: "e",
    relevance: { score, reason: "" },
    evidence: { score: 0, reason: "" },
    structure: { score: 0, reason: "" },
    expression: { score: 0, reason: "" },
    final_score: 0,
  }) as EssayStateType;

describe("routeRelevance", () => {
  it("routes to fan_out when score > 0.5", () => {
    expect(routeRelevance(mkState(0.51))).toBe("fan_out");
  });

  it("routes to calculate_final_score when score = 0.5", () => {
    expect(routeRelevance(mkState(0.5))).toBe("calculate_final_score");
  });

  it("routes to calculate_final_score when score < 0.5", () => {
    expect(routeRelevance(mkState(0.3))).toBe("calculate_final_score");
  });

  it("routes to fan_out when score = 1", () => {
    expect(routeRelevance(mkState(1))).toBe("fan_out");
  });

  it("routes to calculate_final_score when score = 0", () => {
    expect(routeRelevance(mkState(0))).toBe("calculate_final_score");
  });
});
