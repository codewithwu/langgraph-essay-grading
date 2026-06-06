# 历年高考作文题下拉选择 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 GradingPage 作文题目输入框上方加下拉框，选项来自 10 道内置的 2008–2018 年高考作文题（`src/data/articles.md`），选中后回填完整题目（含材料）到输入框；输入框仍可自由输入。

**Architecture:** 用 Vite `?raw` 静态导入 markdown 到 bundle，避免运行时 fetch/CORS 风险；纯函数解析器 `parseArticles` 输出 `Article[]`；FormSection 引入 `ARTICLES` 常量，加 `<select>` 与现有 input 解耦（选中回填，编辑不动 select）；其它代码（GradingPage / 工作流 / settings）一律不动。

**Tech Stack:** Vite 5 (?raw 内置) · React 18 · TypeScript 5 strict · Vitest 2 (jsdom)

---

## File Structure

| 文件 | 状态 | 职责 |
|------|------|------|
| `src/data/articles.md` | **Create** | 10 道高考作文题原始数据（markdown） |
| `src/lib/articles.ts` | **Create** | 纯函数 `parseArticles` + `Article` 类型 + 模块加载时计算的 `ARTICLES` 常量 |
| `src/components/FormSection.tsx` | **Modify** | 在题目 input 上方加 `<select>`，选中回填 |
| `tests/lib/articles.test.ts` | **Create** | 解析器单测（不引入组件测试） |
| `CHANGELOG.md` | **Modify** | `[Unreleased]` 加一条 feat 记录 |
| `README.md` | **Modify** | 使用流程步骤 5 加一句「或从下拉选择题目」 |

---

## Task 1: 创建 articles.md 数据文件

**Files:**
- Create: `src/data/articles.md`

- [ ] **Step 1: 创建文件**

写入完整内容（10 道题，按 2018 → 2008 顺序，每条 `- 标题\n  材料` 格式，材料用 2 空格缩进）：

```markdown
# 历年高考作文题（2008-2018）

- 2018年 全国卷I：「世纪宝宝」与中国梦
  阅读材料，结合2000-2018年发生的大事件（如汶川地震、奥运会、天宫一号等），给2035年的18岁青年写一篇文章。
- 2018年 北京卷：新时代新青年 / 绿水青山
  二选一，议论文谈青年与时代的关系，或记叙文谈生态文明。
- 2017年 全国卷I：从关键词读懂中国
  从来华留学生关注的"一带一路、大熊猫、广场舞、共享单车、长城、高铁、移动支付"等词语中选两三个，帮外国青年读懂中国。
- 2017年 山东卷：24小时书店
  材料作文，谈这家不驱赶任何人（包括流浪者）的书店带给你的思考。
- 2016年 全国卷I：奖惩之后（看图作文）
  根据漫画内容写一篇不少于800字的文章——孩子考100分获吻、98分获掌掴；考55分获掌掴、61分获吻。
- 2015年 广东卷：感知自然
  谈通过不同途径（亲身体验/现代传媒）感知自然的远与近、便利与遗憾。
- 2014年 福建卷：空谷
  根据"提到空谷，有人想到悬崖，有人想到栈道桥梁"这句话写一篇话题作文。
- 2013年 全国卷(大纲卷)：同学关系
  材料作文，探讨高中同学关系紧张的现象及其原因，结合如何增进友谊来写。
- 2012年 福建卷：人生中的赛跑
  引用冯骥才的话："运动中的赛跑...人生中的赛跑，是在有限的时间内看你跑了多少路程"。
- 2008年 全国卷I：汶川地震
  材料作文，围绕抗震救灾中发生的感人事迹、社会各界援助及灾难中展现的民族精神展开。
```

- [ ] **Step 2: 验证文件**

Run: `cat src/data/articles.md | head -5`
Expected: 看到 `# 历年高考作文题（2008-2018）` 标题行

- [ ] **Step 3: 提交**

```bash
git add src/data/articles.md
git commit -m "feat(data): 内置 10 道 2008-2018 年高考作文题"
```

---

## Task 2: 写解析器测试（先失败）

**Files:**
- Create: `tests/lib/articles.test.ts`

- [ ] **Step 1: 写测试文件**

```ts
import { describe, it, expect, vi, beforeEach } from "vitest";
import { parseArticles, type Article } from "../../src/lib/articles";

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
```

- [ ] **Step 2: 跑测试确认失败**

Run: `npm test -- tests/lib/articles.test.ts`
Expected: FAIL（`parseArticles` 尚未实现 → `Cannot find module '../../src/lib/articles'` 或 `parseArticles is not a function`）

---

## Task 3: 实现解析器（让测试通过）

**Files:**
- Create: `src/lib/articles.ts`

- [ ] **Step 1: 实现 `parseArticles` 与 `ARTICLES`**

```ts
import articlesRaw from "../data/articles.md?raw";

export type Article = {
  id: string;
  title: string;
  prompt: string;
};

export function parseArticles(raw: string): Article[] {
  if (typeof raw !== "string") return [];

  const lines = raw.split(/\r?\n/);
  const articles: Article[] = [];
  const yearCounters: Record<string, number> = {};
  let idxFallback = 0;

  let i = 0;
  while (i < lines.length) {
    const line = lines[i];
    const titleMatch = line.match(/^-\s+(.*)$/);
    if (!titleMatch) {
      i++;
      continue;
    }
    const title = titleMatch[1].trim();
    if (!title) {
      console.warn("[articles] skip empty title at line", i + 1);
      i++;
      continue;
    }

    i++;
    const materialLines: string[] = [];
    while (i < lines.length) {
      const ml = lines[i];
      if (/^\s{2,}|\t/.test(ml)) {
        materialLines.push(ml.replace(/^(\s{2,}|\t)/, ""));
        i++;
      } else {
        break;
      }
    }

    const prompt =
      materialLines.length > 0
        ? [title, ...materialLines].join("\n")
        : title;

    const yearMatch = title.match(/\d{4}/);
    let id: string;
    if (yearMatch) {
      const year = yearMatch[0];
      yearCounters[year] = (yearCounters[year] ?? 0) + 1;
      id = `${year}-${yearCounters[year]}`;
    } else {
      idxFallback += 1;
      id = `idx-${idxFallback}`;
    }

    articles.push({ id, title, prompt });
  }

  return articles;
}

export const ARTICLES: Article[] = parseArticles(articlesRaw);
```

- [ ] **Step 2: 跑测试确认通过**

Run: `npm test -- tests/lib/articles.test.ts`
Expected: PASS（8 个 case 全绿）

- [ ] **Step 3: 类型检查**

Run: `npx tsc --noEmit`
Expected: 无错误（`vite/client` 类型声明已为 `?raw` 提供 `string` 返回类型）

- [ ] **Step 4: 提交**

```bash
git add src/lib/articles.ts tests/lib/articles.test.ts
git commit -m "feat(articles): 实现 parseArticles 解析器并补单测"
```

---

## Task 4: 修改 FormSection 加下拉选择

**Files:**
- Modify: `src/components/FormSection.tsx`

- [ ] **Step 1: 替换整个文件内容**

```tsx
import { useState, type FormEvent } from "react";
import { ARTICLES } from "../lib/articles";

type Props = {
  disabled: boolean;
  onSubmit: (topic: string, essay: string) => void;
};

export function FormSection({ disabled, onSubmit }: Props) {
  const [topic, setTopic] = useState("");
  const [essay, setEssay] = useState("");
  const [selectedArticleId, setSelectedArticleId] = useState("");

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    const t = topic.trim();
    const es = essay.trim();
    if (!t || !es) {
      alert("请填写作文题目和内容");
      return;
    }
    onSubmit(t, es);
  }

  function handleArticleChange(id: string) {
    setSelectedArticleId(id);
    if (!id) return;
    const a = ARTICLES.find((x) => x.id === id);
    if (a) setTopic(a.prompt);
  }

  return (
    <form className="form-section" onSubmit={handleSubmit}>
      <div className="form-group">
        <label htmlFor="topic">作文题目</label>
        <select
          id="article-select"
          className="article-select"
          value={selectedArticleId}
          onChange={(e) => handleArticleChange(e.target.value)}
          disabled={disabled}
        >
          <option value="">—— 选择题目 ——</option>
          {ARTICLES.map((a) => (
            <option key={a.id} value={a.id}>
              {a.title}
            </option>
          ))}
        </select>
        <input
          type="text"
          id="topic"
          placeholder="请输入或选择作文题目..."
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
          disabled={disabled}
        />
      </div>
      <div className="form-group">
        <label htmlFor="essay">作文内容</label>
        <textarea
          id="essay"
          placeholder="请输入作文内容..."
          value={essay}
          onChange={(e) => setEssay(e.target.value)}
          disabled={disabled}
        />
      </div>
      <button type="submit" className="btn-submit" disabled={disabled}>
        {disabled ? "评分中..." : "开始评分"}
      </button>
    </form>
  );
}
```

- [ ] **Step 2: 跑类型检查**

Run: `npx tsc --noEmit`
Expected: 无错误

- [ ] **Step 3: 跑全部测试**

Run: `npm test`
Expected: 全部通过（包括之前的 hooks / workflow / settings 测试与新加的 articles 测试）

- [ ] **Step 4: 跑 lint**

Run: `npm run lint`
Expected: 无错误（若报 `react-hooks/exhaustive-deps` 之类，需检查 select onChange 是否引用稳定值；当前实现只用 setState 不会有 deps 问题）

- [ ] **Step 5: 提交**

```bash
git add src/components/FormSection.tsx
git commit -m "feat(grading): 作文题目支持从内置题库下拉选择"
```

---

## Task 5: 更新 CHANGELOG 与 README

**Files:**
- Modify: `CHANGELOG.md`
- Modify: `README.md`

- [ ] **Step 1: 在 `CHANGELOG.md` 顶部 `[Unreleased]` 段下加一条**

查找 `## [Unreleased]` 段（若不存在则在文件顶部新建），在该段已有条目后追加：

```markdown
- feat(grading): 内置 10 道历年高考作文题（2008-2018），支持下拉选择回填到题目输入框
```

- [ ] **Step 2: 改 `README.md` 使用流程步骤 5**

把第 5 步：

```markdown
5. 输入作文题目与内容，点「开始评分」
```

改为：

```markdown
5. 输入作文题目与内容（或从下拉选择内置的历年高考题），点「开始评分」
```

- [ ] **Step 3: 提交**

```bash
git add CHANGELOG.md README.md
git commit -m "docs: 记录内置题库下拉选择与 README 使用流程"
```

---

## Task 6: 最终验证

**Files:** 无（仅跑命令）

- [ ] **Step 1: 跑全套质量门禁**

```bash
npx tsc --noEmit
npm run lint
npm test
npm run build
```

Expected:
- `tsc --noEmit` 无错误
- `npm run lint` 无错误
- `npm test` 全部通过
- `npm run build` 产出 `dist/`，无错误

- [ ] **Step 2: 跑 dev server 肉眼验证**

```bash
npm run dev
```

打开 `http://localhost:5173`，确认：
- 「作文题目」标签下方先看到下拉框（默认 "—— 选择题目 ——"），再看到输入框
- 选中任一选项 → 输入框被填上「年份+卷别+标题\n材料」
- 手动修改输入框内容 → 下拉框选中状态不变
- 切换页面再回来 → 输入框保持用户最后一次输入（不持久化到 localStorage，符合现有行为）

- [ ] **Step 3: 提交（若 dev 验证发现代码调整）**

如有调整则 `git add` + `git commit -m "fix(grading): dev 验证后微调"`；无调整则跳过。

---

## Self-Review Checklist

- [x] **Spec 覆盖**：
  - §3 数据格式 → Task 1（articles.md 内容）+ Task 2 fixture
  - §4 解析器规则 → Task 2 测试 + Task 3 实现
  - §5 UI 改动 → Task 4
  - §7 测试 → Task 2 + Task 3 步骤 2
  - §8 文档变更 → Task 5
  - §9 范围外 → 已显式不引入组件测试、不动 GradingPage
- [x] **占位符扫描**：无 TBD / TODO / "实现具体内容"
- [x] **类型一致性**：`Article` / `parseArticles` / `ARTICLES` / `Article.id` / `Article.title` / `Article.prompt` 在 Task 2/3/4 间一致
