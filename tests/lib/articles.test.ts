import { describe, it, expect, vi, beforeEach } from "vitest";
import { parseArticles } from "../../src/lib/articles";

const FIXTURE = `# 历年高考作文题（2008-2018）

- 2018年 全国卷I：「世纪宝宝」与中国梦
  阅读材料，结合2000-2018年发生的大事件。
- 2018年 北京卷：新时代新青年 / 绿水青山
  二选一，议论文谈青年与时代的关系。
- 2017年 全国卷I：从关键词读懂中国
  从词语中选两三个。
- 2017年 山东卷：24小时书店
  谈这家书店带给你的思考。
  第二个材料行。
- 2008年 全国卷I：汶川地震
  围绕抗震救灾展开。
- 无年份条目
  这条没有 4 位年份。
`;

describe("parseArticles", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("parses basic entries with title and material", () => {
    const result = parseArticles(FIXTURE);
    expect(result).toHaveLength(6);
    expect(result[0].title).toBe("2018年 全国卷I：「世纪宝宝」与中国梦");
    expect(result[0].prompt).toBe(
      "2018年 全国卷I：「世纪宝宝」与中国梦\n阅读材料，结合2000-2018年发生的大事件。"
    );
  });

  it("joins multi-line material with \\n", () => {
    const result = parseArticles(FIXTURE);
    const sdBookstore = result.find((a) => a.title.includes("24小时书店"));
    expect(sdBookstore).toBeDefined();
    expect(sdBookstore!.prompt).toBe(
      "2017年 山东卷：24小时书店\n谈这家书店带给你的思考。\n第二个材料行。"
    );
  });

  it("generates id from first 4-digit year + per-year counter", () => {
    const result = parseArticles(FIXTURE);
    expect(result[0].id).toBe("2018-1");
    expect(result[1].id).toBe("2018-2");
    expect(result[2].id).toBe("2017-1");
    expect(result[3].id).toBe("2017-2");
    expect(result[4].id).toBe("2008-1");
  });

  it("uses idx-N fallback id when no 4-digit year in title", () => {
    const result = parseArticles(FIXTURE);
    const noYear = result.find((a) => a.title === "无年份条目");
    expect(noYear).toBeDefined();
    expect(noYear!.id).toBe("idx-1");
  });

  it("skips empty titles and warns", () => {
    const warn = vi.spyOn(console, "warn").mockImplementation(() => {});
    const raw = "- \n  材料\n- 有效标题\n  材料";
    const result = parseArticles(raw);
    expect(result).toHaveLength(1);
    expect(result[0].title).toBe("有效标题");
    expect(warn).toHaveBeenCalled();
  });

  it("prompt equals title when material is missing", () => {
    const raw = "- 仅标题\n- 标题\n  材料";
    const result = parseArticles(raw);
    expect(result[0].prompt).toBe("仅标题");
    expect(result[1].prompt).toBe("标题\n材料");
  });

  it("returns empty array on non-string input", () => {
    // @ts-expect-error testing runtime guard
    expect(parseArticles(undefined)).toEqual([]);
    // @ts-expect-error testing runtime guard
    expect(parseArticles(null)).toEqual([]);
  });

  it("preserves source order", () => {
    const result = parseArticles(FIXTURE);
    expect(result.map((a) => a.title)).toEqual([
      "2018年 全国卷I：「世纪宝宝」与中国梦",
      "2018年 北京卷：新时代新青年 / 绿水青山",
      "2017年 全国卷I：从关键词读懂中国",
      "2017年 山东卷：24小时书店",
      "2008年 全国卷I：汶川地震",
      "无年份条目",
    ]);
  });
});
