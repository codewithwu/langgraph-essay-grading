import { describe, it, expect } from "vitest";
import {
  GAOKAO_DIMS,
  STANDARD_DIMS,
  getDimensions,
  getWeights,
  getLabel,
  type Dim,
} from "../../src/workflow/dimensions";

describe("dimensions", () => {
  it("STANDARD 维度数 = 4, 权重和 = 1", () => {
    expect(STANDARD_DIMS).toHaveLength(4);
    const sum = STANDARD_DIMS.reduce((s, d) => s + d.weight, 0);
    expect(sum).toBeCloseTo(1, 6);
  });

  it("GAOKAO 维度数 = 7, 权重和 = 1", () => {
    expect(GAOKAO_DIMS).toHaveLength(7);
    const sum = GAOKAO_DIMS.reduce((s, d) => s + d.weight, 0);
    expect(sum).toBeCloseTo(1, 6);
  });

  it("GAOKAO 各维度权重 = 1/7", () => {
    for (const d of GAOKAO_DIMS) {
      expect(d.weight).toBeCloseTo(1 / 7, 6);
    }
  });

  it("getDimensions(standard) 与 STANDARD_DIMS 引用相等", () => {
    expect(getDimensions("standard")).toBe(STANDARD_DIMS);
  });

  it("getDimensions(gaokao) 与 GAOKAO_DIMS 引用相等", () => {
    expect(getDimensions("gaokao")).toBe(GAOKAO_DIMS);
  });

  it("getWeights 返回的 Map 以 field 为键,权重正确", () => {
    const w = getWeights("gaokao");
    for (const d of GAOKAO_DIMS) {
      expect(w.get(d.field)).toBeCloseTo(d.weight, 6);
    }
  });

  it("getLabel 对每个维度返回非空中文标签", () => {
    const allDims: Dim[] = [...STANDARD_DIMS, ...GAOKAO_DIMS];
    for (const d of allDims) {
      const label = getLabel(d.node);
      expect(label).toBeTruthy();
      expect(typeof label).toBe("string");
      expect(label.length).toBeGreaterThan(0);
    }
  });

  it("每种模式内节点名唯一(无冲突)", () => {
    function uniqueCount(arr: readonly { node: string }[]): number {
      return new Set(arr.map((d) => d.node)).size;
    }
    expect(uniqueCount(STANDARD_DIMS)).toBe(STANDARD_DIMS.length);
    expect(uniqueCount(GAOKAO_DIMS)).toBe(GAOKAO_DIMS.length);
  });
});
