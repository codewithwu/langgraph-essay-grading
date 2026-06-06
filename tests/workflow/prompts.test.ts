import { describe, it, expect } from "vitest";
import { z } from "zod";
import { STANDARD_SYSTEM_PROMPT, buildPrompt } from "../../src/workflow/prompts";

const TestSchema = z.object({
  score: z.number(),
  label: z.string(),
}).describe("TestSchema");

describe("buildPrompt", () => {
  it("includes schema name", () => {
    const p = buildPrompt(TestSchema);
    expect(p).toContain("TestSchema");
  });

  it("includes score and label property names from schema", () => {
    const p = buildPrompt(TestSchema);
    expect(p).toContain("score");
    expect(p).toContain("label");
  });

  it("instructs JSON-only output", () => {
    const p = buildPrompt(TestSchema);
    expect(p.toLowerCase()).toContain("json");
  });
});

describe("STANDARD_SYSTEM_PROMPT", () => {
  it("mentions 高考", () => {
    expect(STANDARD_SYSTEM_PROMPT).toContain("高考");
  });

  it("specifies score range 0~1", () => {
    expect(STANDARD_SYSTEM_PROMPT).toMatch(/0[~～-]1|0\s*到\s*1/);
  });
});
