# 高考作文模式（7 维度 + w.md 评分标准）Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 GradingPage 增加「高考作文模式」切换。开启后，评分工作流从 4 维度升级为 7 维度（审题立意 / 内容论据 / 篇章结构 / 语言文采 / 思想深度 / 创新创意 / 卷面格式），覆盖 w.md 的「基础 + 发展 + 卷面」评分标准；关闭后保持现有 4 维度行为。总分仍以 1.00 满分。

**Architecture:** 双 graph 架构。`workflow/dimensions.ts` 集中管理两套维度与权重；`workflow/graph.ts` 编译 `standardGraph` 与 `gaokaoGraph`，通过 `getGraph(mode)` 选择；`useGradingStream` 按 mode 路由。Mode 选择存 localStorage，默认 gaokao。前端在 FormSection 顶部加 ModeToggle。

**Tech Stack:** React 18, TypeScript 5, Vite 5, @langchain/langgraph, @langchain/openai, Zod, Vitest, React Testing Library

---

## File Structure

### 新增文件
- `src/lib/mode-storage.ts` — 模式读写 localStorage
- `src/workflow/dimensions.ts` — 维度定义 / 权重 / 标签集中管理
- `src/components/ModeToggle.tsx` — 切换按钮组件
- `tests/lib/mode-storage.test.ts` — mode 存储单测
- `tests/workflow/dimensions.test.ts` — 维度配置单测

### 修改文件
- `src/workflow/config.ts` — `NODE_NAMES` 扩展；删除 `WEIGHT_*`（迁入 dimensions.ts）；保留 `RELEVANCE_THRESHOLD`
- `src/workflow/state.ts` — `EssayState` 新增 4 个 gaokao 字段
- `src/workflow/prompts.ts` — `SYSTEM_PROMPT` 拆为 `STANDARD_SYSTEM_PROMPT` 与 `GAOKAO_SYSTEM_PROMPT`
- `src/workflow/nodes.ts` — 改用 `getInstructions(mode, dim)`，每个 gaokao 节点对应一段完整 w.md 描述
- `src/workflow/graph.ts` — 编译双 graph，导出 `getGraph(mode)`；`calculate_final_score` 改用 `getWeights(mode)`
- `src/hooks/useGradingStream.ts` — `run()` 接收 `mode`
- `src/components/FormSection.tsx` — 顶部插入 `ModeToggle`
- `src/pages/GradingPage.tsx` — 维护 mode state、持久化、按 mode 渲染
- `src/styles/index.css` — `.mode-toggle` 样式
- `tests/pages/GradingPage.test.tsx` — 新增 mode 切换与持久化 case
- `CHANGELOG.md` — 记录 Added / Changed
- `README.md` — 维度表扩展 + 模式说明

### 不修改
- `src/components/ScoreCard.tsx`、`src/components/FinalScoreCard.tsx`、`src/components/SkeletonCard.tsx`、`src/components/LoadingBar.tsx`、`src/components/Header.tsx`、`src/hooks/useQuota.ts`、`src/lib/quota.ts`、`src/lib/articles.ts`、`src/lib/settings.ts`、`src/config/llm-defaults.json`

---

## Task 1: 模式存储模块（mode-storage.ts）

**Files:**
- Create: `src/lib/mode-storage.ts`
- Create: `tests/lib/mode-storage.test.ts`

- [ ] **Step 1: 写失败测试**

`tests/lib/mode-storage.test.ts`:

```ts
import { describe, it, expect, beforeEach, vi } from "vitest";
import { loadMode, saveMode, DEFAULT_MODE, type Mode } from "../../src/lib/mode-storage";

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
  });

  it("localStorage 抛错时 save 静默失败", () => {
    const setItem = vi.spyOn(Storage.prototype, "setItem").mockImplementation(() => {
      throw new Error("quota");
    });
    expect(() => saveMode("standard")).not.toThrow();
    setItem.mockRestore();
  });
});
```

- [ ] **Step 2: 跑测试确认失败**

Run: `npx vitest run tests/lib/mode-storage.test.ts`
Expected: FAIL — module not found

- [ ] **Step 3: 实现 mode-storage.ts**

`src/lib/mode-storage.ts`:

```ts
const STORAGE_KEY = "grading-mode-v1";
const VALID_MODES = ["standard", "gaokao"] as const;
export type Mode = (typeof VALID_MODES)[number];
export const DEFAULT_MODE: Mode = "gaokao";

function isValidMode(v: unknown): v is Mode {
  return typeof v === "string" && (VALID_MODES as readonly string[]).includes(v);
}

export function loadMode(): Mode {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw === null) return DEFAULT_MODE;
    const parsed: unknown = JSON.parse(raw);
    if (!isValidMode(parsed)) {
      console.warn(`[mode-storage] 非法 mode 值 "${String(parsed)}" 已回退为 ${DEFAULT_MODE}`);
      return DEFAULT_MODE;
    }
    return parsed;
  } catch (err) {
    console.warn(`[mode-storage] 读取失败,回退默认:`, err);
    return DEFAULT_MODE;
  }
}

export function saveMode(mode: Mode): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(mode));
  } catch (err) {
    console.warn(`[mode-storage] 写入失败(忽略):`, err);
  }
}
```

- [ ] **Step 4: 跑测试确认通过**

Run: `npx vitest run tests/lib/mode-storage.test.ts`
Expected: 5 passed

- [ ] **Step 5: 提交**

```bash
git add src/lib/mode-storage.ts tests/lib/mode-storage.test.ts
git commit -m "feat(mode): 新增 mode 读写 localStorage 模块"
```

---

## Task 2: 维度配置模块（dimensions.ts）

**Files:**
- Create: `src/workflow/dimensions.ts`
- Create: `tests/workflow/dimensions.test.ts`

- [ ] **Step 1: 写失败测试**

`tests/workflow/dimensions.test.ts`:

```ts
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

  it("getWeights 返回的 Map 包含所有节点名", () => {
    const w = getWeights("gaokao");
    for (const d of GAOKAO_DIMS) {
      expect(w.get(d.node)).toBeCloseTo(d.weight, 6);
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

  it("节点名跨模式唯一(无冲突)", () => {
    const stdNames = new Set(STANDARD_DIMS.map((d) => d.node));
    const gkNames = GAOKAO_DIMS.map((d) => d.node);
    for (const n of gkNames) {
      expect(stdNames.has(n)).toBe(false);
    }
  });
});
```

- [ ] **Step 2: 跑测试确认失败**

Run: `npx vitest run tests/workflow/dimensions.test.ts`
Expected: FAIL — module not found

- [ ] **Step 3: 实现 dimensions.ts**

`src/workflow/dimensions.ts`:

```ts
import type { Mode } from "../lib/mode-storage";

export type Dim = {
  /** LangGraph 节点名 */
  node: string;
  /** EssayState 中的字段名(节点输出会写入该字段) */
  field: string;
  /** 中文标签,用于 UI 卡片标题 */
  label: string;
  /** 0-1 之间的权重;所有 dim 权重和必须 = 1 */
  weight: number;
};

export const STANDARD_DIMS: readonly Dim[] = [
  { node: "check_relevance", field: "relevance", label: "审题立意", weight: 0.3 },
  { node: "check_evidence", field: "evidence", label: "论据分析", weight: 0.2 },
  { node: "check_structure", field: "structure", label: "结构评估", weight: 0.2 },
  { node: "check_expression", field: "expression", label: "语言文采", weight: 0.3 },
];

export const GAOKAO_DIMS: readonly Dim[] = [
  { node: "check_relevance", field: "relevance", label: "审题立意", weight: 1 / 7 },
  { node: "check_content", field: "content", label: "内容论据", weight: 1 / 7 },
  { node: "check_structure", field: "structure", label: "篇章结构", weight: 1 / 7 },
  { node: "check_expression", field: "expression", label: "语言文采", weight: 1 / 7 },
  { node: "check_depth", field: "depth", label: "思想深度", weight: 1 / 7 },
  { node: "check_novelty", field: "novelty", label: "创新创意", weight: 1 / 7 },
  { node: "check_formatting", field: "formatting", label: "卷面格式", weight: 1 / 7 },
];

export function getDimensions(mode: Mode): readonly Dim[] {
  return mode === "gaokao" ? GAOKAO_DIMS : STANDARD_DIMS;
}

export function getWeights(mode: Mode): Map<string, number> {
  const dims = getDimensions(mode);
  const m = new Map<string, number>();
  for (const d of dims) m.set(d.field, d.weight);
  return m;
}

export function getLabel(node: string): string {
  const all = [...STANDARD_DIMS, ...GAOKAO_DIMS];
  return all.find((d) => d.node === node)?.label ?? node;
}
```

- [ ] **Step 4: 跑测试确认通过**

Run: `npx vitest run tests/workflow/dimensions.test.ts`
Expected: 8 passed

- [ ] **Step 5: 提交**

```bash
git add src/workflow/dimensions.ts tests/workflow/dimensions.test.ts
git commit -m "feat(workflow): 新增 dimensions 配置,集中管理维度与权重"
```

---

## Task 3: 扩展 NODE_NAMES + 移除旧 WEIGHT_*

**Files:**
- Modify: `src/workflow/config.ts`

- [ ] **Step 1: 替换 config.ts**

`src/workflow/config.ts` 完整内容:

```ts
export const RELEVANCE_THRESHOLD = 0.5;

export const NODE_NAMES = {
  RELEVANCE: "check_relevance",
  EVIDENCE: "check_evidence",
  STRUCTURE: "check_structure",
  EXPRESSION: "check_expression",
  CONTENT: "check_content",
  DEPTH: "check_depth",
  NOVELTY: "check_novelty",
  FORMATTING: "check_formatting",
  FAN_OUT: "fan_out",
  CALCULATE: "calculate_final_score",
} as const;
```

注：`WEIGHT_RELEVANCE` / `WEIGHT_EVIDENCE` / `WEIGHT_STRUCTURE` / `WEIGHT_EXPRESSION` 从本文件删除，已迁入 `dimensions.ts`。

- [ ] **Step 2: 跑现有测试找引用方**

Run: `npx tsc --noEmit`
Expected: 报错 — `src/workflow/nodes.ts` 和 `src/workflow/graph.ts` 引用了已删除的 `WEIGHT_*`

- [ ] **Step 3: 提交(仅 config 改动)**

```bash
git add src/workflow/config.ts
git commit -m "refactor(workflow): NODE_NAMES 扩展,WEIGHT_* 迁入 dimensions"
```

注：Task 4–7 会修复 nodes.ts / graph.ts 的引用,本任务先单独提交,便于回滚。

---

## Task 4: 扩展 EssayState

**Files:**
- Modify: `src/workflow/state.ts`

- [ ] **Step 1: 替换 state.ts**

`src/workflow/state.ts` 完整内容:

```ts
import { z } from "zod";
import { Annotation } from "@langchain/langgraph";

export const ScoreDetail = z.object({
  score: z.number().min(0).max(1),
  reason: z.string(),
});

export type ScoreDetail = z.infer<typeof ScoreDetail>;

export const EssayState = Annotation.Root({
  topic: Annotation<string>(),
  essay: Annotation<string>(),
  relevance: Annotation<ScoreDetail>(),
  evidence: Annotation<ScoreDetail>(),
  structure: Annotation<ScoreDetail>(),
  expression: Annotation<ScoreDetail>(),
  content: Annotation<ScoreDetail>(),
  depth: Annotation<ScoreDetail>(),
  novelty: Annotation<ScoreDetail>(),
  formatting: Annotation<ScoreDetail>(),
  final_score: Annotation<number>(),
});

export type EssayStateType = typeof EssayState.State;
```

- [ ] **Step 2: 类型检查**

Run: `npx tsc --noEmit`
Expected: 仍报错 (nodes.ts / graph.ts 还没改), 错误数不变

- [ ] **Step 3: 提交**

```bash
git add src/workflow/state.ts
git commit -m "feat(workflow): EssayState 扩展 4 个 gaokao 字段"
```

---

## Task 5: 拆 system prompt

**Files:**
- Modify: `src/workflow/prompts.ts`

- [ ] **Step 1: 替换 prompts.ts**

`src/workflow/prompts.ts` 完整内容:

```ts
import type { z } from "zod";
import { zodToJsonSchema } from "zod-to-json-schema";
import type { Mode } from "../lib/mode-storage";

export const STANDARD_SYSTEM_PROMPT = `你是一名经验丰富的高考语文作文阅卷老师。请遵循以下评分原则：

【评分总则】
1. 严格按照高考语文作文评分标准评判，参考"基础等级"与"发展等级"两项
2. 客观公正，不因作文主题立场、情感倾向而加分或减分
3. 评分理由要具体、有依据，应引用作文原文片段
4. 四个维度独立评分，不因某维度表现好而影响其他维度

【分值区间与等级】
采用 0~1 的连续分值，对应高考 60 分制的五等评分：
- 优秀（一类，0.80~1.00）：内容充实，立意深刻，结构严谨，语言优美
- 良好（二类，0.60~0.79）：内容较充实，立意较深刻，结构完整，语言通顺
- 中等（三类，0.40~0.59）：内容尚可，立意一般，结构基本完整，语言基本通顺
- 较差（四类，0.20~0.39）：内容空洞，立意偏颇，结构不完整，语病较多
- 极差（五类，0.05~0.19）：严重跑题或文不对题，字数严重不足（少于 200 字），或存在明显抄袭痕迹

【关于 0 分】
0 分仅在以下极端情况使用：完全空白卷、与题目毫无关联且无法挽救的跑题卷、整体抄袭原文。
即使是较差或极差的作文，只要考生有写作尝试、围绕题目展开过论述，也应给予 0.05 以上的分数，以体现"分值梯度的连续性"和"对写作努力的认可"。
切忌将"立意肤浅""论据陈旧""结构松散""语言平淡"等常见问题直接判 0 分——这些应落入 0.20~0.40 区间。
及格线为 0.60。`;

export const GAOKAO_SYSTEM_PROMPT = `你是一名经验丰富的高考语文作文阅卷老师。请严格按教育部考试中心《高考语文作文评分标准》(基础等级 40 分 + 发展等级 20 分) 评判,七维度独立评分。

【基础等级 40 分】
- 内容 20 分:题意、中心、内容、思想、感情
  * 一等(16~20):符合题意 中心突出 内容充实 思想健康 感情真挚
  * 二等(11~15):符合题意 中心明确 内容较充实 思想健康 感情真实
  * 三等(6~10):基本符合题意 中心基本明确 内容单薄 思想基本健康 感情基本真实
  * 四等(0~5):偏离题意 中心不明确 内容不当 思想不健康 感情虚假
- 表达 20 分:结构、语言、文体、卷面
  * 一等(16~20):符合文体要求 结构严谨 语言流畅 字迹工整
  * 二等(11~15):符合文体要求 结构完整 语言通顺 字迹清楚
  * 三等(6~10):基本符合文体要求 结构基本完整 语言基本通顺 字迹基本清楚
  * 四等(0~5):不符合文体要求 结构混乱 语言不通顺、语病多 字迹潦草难辨

【发展等级 20 分(特征 4 项 16 点)】
1. 深刻:①透过现象看本质 ②揭示事物内在的因果关系 ③观点具有启发作用
2. 丰富:④材料丰富 ⑤论据充足 ⑥形象丰满 ⑦意境深远
3. 有文采:⑧用词贴切 ⑨句式灵活 ⑩善于运用修辞手法 ⑪文句有表现力
4. 有创意:⑫见解新颖 ⑬材料新鲜 ⑭构思精巧 ⑮推理想象有独到之处 ⑯有个性特征

【扣分细则】
- 错别字:1 个扣 1 分,重复不计,扣完 5 分为止
- 标点:3 处以上错误酌情扣分
- 字数:不足字数者,每少 50 字扣 1 分
- 标题:无标题扣 2 分

【残篇评定】
- 400 字以上:按评分标准评分,扣字数分
- 400 字以下:20 分以下评分,不再扣字数分
- 200 字以下:10 分以下评分
- 只写一两句话:给 1 或 2 分,不评 0 分
- 完全空白:评 0 分

【分值区间与等级】
采用 0~1 的连续分值:
- 优秀(一类,0.80~1.00):一类文 54~60 分
- 良好(二类,0.60~0.79):二类文 48~53 分
- 中等(三类,0.40~0.59):三类文 42~47 分
- 较差(四类,0.20~0.39):四类文 36~41 分
- 极差(五类,0.05~0.19):五类文 35 分及以下

【关于 0 分】
0 分仅在完全空白、整体抄袭等极端情况使用。
有写作尝试但表现差的,至少给 0.05。
及格线为 0.60。`;

export function getSystemPrompt(mode: Mode): string {
  return mode === "gaokao" ? GAOKAO_SYSTEM_PROMPT : STANDARD_SYSTEM_PROMPT;
}

export function buildPrompt(schema: z.ZodTypeAny): string {
  const schemaName = schema.description ?? "Output";
  const schemaJson = JSON.stringify(zodToJsonSchema(schema), null, 2);
  return `你是一个 JSON 输出助手。
【输出规则】
1. 只输出纯 JSON 对象，不要包含任何解释、markdown 代码块或其他内容
2. 根据输入内容判断：从用户的输入中提取有效的 ${schemaName} 信息
3. 确保 JSON 字段与 Schema 定义完全一致

【Schema 定义】
## ${schemaName}
${schemaJson}
`;
}
```

- [ ] **Step 2: 类型检查**

Run: `npx tsc --noEmit`
Expected: 仍报错 (旧 nodes.ts 引用了 `SYSTEM_PROMPT`), 后续 task 修

- [ ] **Step 3: 提交**

```bash
git add src/workflow/prompts.ts
git commit -m "refactor(workflow): 拆 system prompt 为 standard/gaokao 两套"
```

---

## Task 6: 重构 nodes.ts

**Files:**
- Modify: `src/workflow/nodes.ts`

- [ ] **Step 1: 替换 nodes.ts**

`src/workflow/nodes.ts` 完整内容:

```ts
import { HumanMessage, SystemMessage } from "@langchain/core/messages";
import { ScoreDetail, type EssayStateType } from "./state";
import { buildPrompt, getSystemPrompt } from "./prompts";
import { getLLM } from "./llm";
import type { Mode } from "../lib/mode-storage";

type Dim =
  | "relevance"
  | "evidence"
  | "structure"
  | "expression"
  | "content"
  | "depth"
  | "novelty"
  | "formatting";

const DIM_INSTRUCTIONS: Record<Mode, Record<Dim, string>> = {
  standard: {
    relevance: "请评估以下高考作文的「审题立意」维度。考察是否紧扣题目材料、中心是否明确、立意是否深刻、是否有独到见解。重点关注是否切题、是否扣题写作，以及立意的高度与深度。",
    evidence: "请评估以下高考作文的「论据分析」维度。考察材料是否充实、论据是否典型、论证是否有力、事例与观点是否一致。议论文重点看论证方法（举例、对比、比喻、类比等）是否有效；记叙文或散文则看细节、情感是否支撑主旨。",
    structure: "请评估以下高考作文的「篇章结构」维度。考察段落安排、层次推进、过渡衔接、首尾呼应、行文逻辑是否连贯。重点关注是否结构完整、条理清晰、过渡自然。",
    expression: "请评估以下高考作文的「语言表达」维度。考察用词是否贴切、句式是否灵活、修辞是否恰当、是否有文采和意蕴。允许适度的个性化表达，关注整体语言质量而非单点瑕疵。",
  },
  gaokao: {
    relevance: "请评估「审题立意」维度(对应 w.md 基础等级「内容」项的题意/中心/思想/感情):是否切题、中心是否突出、是否符合题意所涉及的范围/情境/任务要求;立意是否准确、集中、鲜明,有无独到见解。",
    content: "请评估「内容论据」维度(对应 w.md 基础等级「内容」项的材料/论据):内容是否充实、论据是否典型/充足、事例与观点是否一致;议论文看论证方法(举例、对比、比喻、类比等)是否有效;记叙文或散文看细节、情感是否支撑主旨。",
    structure: "请评估「篇章结构」维度(对应 w.md 基础等级「表达」项的结构):段落安排、层次推进、过渡衔接、首尾呼应、行文逻辑是否连贯;是否结构严谨、条理清晰、过渡自然。",
    expression: "请评估「语言文采」维度(对应 w.md 基础等级「表达」项的语言 + 发展等级「有文采」):用词是否贴切、句式是否灵活、修辞是否得当、文句有无表现力;关注整体语言质量与文采,允许适度个性化表达。",
    depth: "请评估「思想深度」维度(对应 w.md 发展等级「深刻」):①是否透过现象看本质 ②是否揭示事物内在的因果关系 ③观点是否具有启发作用。三点居其一即可得高分。",
    novelty: "请评估「创新创意」维度(对应 w.md 发展等级「有创意」):①见解是否新颖 ②材料是否新鲜 ③构思是否精巧 ④推理想象有无独到之处 ⑤是否有个性特征。",
    formatting: "请评估「卷面格式」维度(对应 w.md 扣分细则):错别字数量(1 字扣 1 分,重复不计,封顶 5 分)、标点错误(3 处以上酌情扣分)、字数是否达标(每少 50 字扣 1 分)、是否有标题(无标题扣 2 分)。综合上述给出 0-1 分数(1.00 = 无任何扣分项)。",
  },
};

async function gradeDim(
  state: EssayStateType,
  mode: Mode,
  dim: Dim,
): Promise<Partial<EssayStateType>> {
  const llm = getLLM().withStructuredOutput(ScoreDetail);
  const messages = [
    new SystemMessage(buildPrompt(ScoreDetail) + getSystemPrompt(mode)),
    new HumanMessage(
      `${DIM_INSTRUCTIONS[mode][dim]}\n给出 0 到 1 之间的分数，并说明理由。\n\n题目：${state.topic}\n\n作文：${state.essay}`,
    ),
  ];
  return { [dim]: await llm.invoke(messages) } as Partial<EssayStateType>;
}

export async function check_relevance(
  state: EssayStateType,
): Promise<Partial<EssayStateType>> {
  const mode = state._mode ?? "standard";
  return gradeDim(state, mode, "relevance");
}

export async function check_evidence(
  state: EssayStateType,
): Promise<Partial<EssayStateType>> {
  return gradeDim(state, "standard", "evidence");
}

export async function check_structure(
  state: EssayStateType,
): Promise<Partial<EssayStateType>> {
  const mode = state._mode ?? "standard";
  return gradeDim(state, mode, "structure");
}

export async function check_expression(
  state: EssayStateType,
): Promise<Partial<EssayStateType>> {
  const mode = state._mode ?? "standard";
  return gradeDim(state, mode, "expression");
}

export async function check_content(
  state: EssayStateType,
): Promise<Partial<EssayStateType>> {
  return gradeDim(state, "gaokao", "content");
}

export async function check_depth(
  state: EssayStateType,
): Promise<Partial<EssayStateType>> {
  return gradeDim(state, "gaokao", "depth");
}

export async function check_novelty(
  state: EssayStateType,
): Promise<Partial<EssayStateType>> {
  return gradeDim(state, "gaokao", "novelty");
}

export async function check_formatting(
  state: EssayStateType,
): Promise<Partial<EssayStateType>> {
  return gradeDim(state, "gaokao", "formatting");
}

export function calculate_final_score(
  state: EssayStateType,
): Partial<EssayStateType> {
  const mode = state._mode ?? "standard";
  const weights = mode === "gaokao"
    ? {
        relevance: 1 / 7,
        content: 1 / 7,
        structure: 1 / 7,
        expression: 1 / 7,
        depth: 1 / 7,
        novelty: 1 / 7,
        formatting: 1 / 7,
      }
    : {
        relevance: 0.3,
        evidence: 0.2,
        structure: 0.2,
        expression: 0.3,
      };

  const final = (Object.entries(weights) as [keyof typeof weights, number][])
    .reduce((sum, [field, w]) => {
      const detail = state[field];
      return sum + (detail?.score ?? 0) * w;
    }, 0);

  return { final_score: Math.round(final * 100) / 100 };
}
```

- [ ] **Step 2: 类型检查(预期失败)**

Run: `npx tsc --noEmit`
Expected: 报错 — `_mode` 不在 `EssayStateType` 上

- [ ] **Step 3: 提交(允许编译失败,留待 Task 7 修复)**

```bash
git add src/workflow/nodes.ts
git commit -m "refactor(workflow): nodes.ts 拆为 standard/gaokao 两套指令"
```

---

## Task 7: 扩展 state + 编译双 graph

**Files:**
- Modify: `src/workflow/state.ts` (再次修改,加 `_mode`)
- Modify: `src/workflow/graph.ts` (重写)

- [ ] **Step 1: 修改 state.ts 加 `_mode` 字段**

替换 `src/workflow/state.ts` 为:

```ts
import { z } from "zod";
import { Annotation } from "@langchain/langgraph";
import type { Mode } from "../lib/mode-storage";

export const ScoreDetail = z.object({
  score: z.number().min(0).max(1),
  reason: z.string(),
});

export type ScoreDetail = z.infer<typeof ScoreDetail>;

export const EssayState = Annotation.Root({
  topic: Annotation<string>(),
  essay: Annotation<string>(),
  _mode: Annotation<Mode>(),
  relevance: Annotation<ScoreDetail>(),
  evidence: Annotation<ScoreDetail>(),
  structure: Annotation<ScoreDetail>(),
  expression: Annotation<ScoreDetail>(),
  content: Annotation<ScoreDetail>(),
  depth: Annotation<ScoreDetail>(),
  novelty: Annotation<ScoreDetail>(),
  formatting: Annotation<ScoreDetail>(),
  final_score: Annotation<number>(),
});

export type EssayStateType = typeof EssayState.State;
```

- [ ] **Step 2: 替换 graph.ts**

`src/workflow/graph.ts` 完整内容:

```ts
import { END, START, StateGraph } from "@langchain/langgraph";
import { EssayState, type EssayStateType } from "./state";
import {
  calculate_final_score,
  check_content,
  check_depth,
  check_evidence,
  check_expression,
  check_formatting,
  check_novelty,
  check_relevance,
  check_structure,
} from "./nodes";
import { routeRelevance } from "./routes";
import { NODE_NAMES } from "./config";
import type { Mode } from "../lib/mode-storage";

function fanOut(_: EssayStateType): Record<string, never> {
  return {};
}

// 标准模式: 4 维(evidence / structure / expression 并行)
export const standardGraph = new StateGraph(EssayState)
  .addNode(NODE_NAMES.RELEVANCE, check_relevance)
  .addNode(NODE_NAMES.FAN_OUT, fanOut)
  .addNode(NODE_NAMES.EVIDENCE, check_evidence)
  .addNode(NODE_NAMES.STRUCTURE, check_structure)
  .addNode(NODE_NAMES.EXPRESSION, check_expression)
  .addNode(NODE_NAMES.CALCULATE, calculate_final_score)
  .addEdge(START, NODE_NAMES.RELEVANCE)
  .addConditionalEdges(NODE_NAMES.RELEVANCE, routeRelevance, {
    fan_out: NODE_NAMES.FAN_OUT,
    calculate_final_score: NODE_NAMES.CALCULATE,
  })
  .addEdge(NODE_NAMES.FAN_OUT, NODE_NAMES.EVIDENCE)
  .addEdge(NODE_NAMES.FAN_OUT, NODE_NAMES.STRUCTURE)
  .addEdge(NODE_NAMES.FAN_OUT, NODE_NAMES.EXPRESSION)
  .addEdge(NODE_NAMES.EVIDENCE, NODE_NAMES.CALCULATE)
  .addEdge(NODE_NAMES.STRUCTURE, NODE_NAMES.CALCULATE)
  .addEdge(NODE_NAMES.EXPRESSION, NODE_NAMES.CALCULATE)
  .addEdge(NODE_NAMES.CALCULATE, END)
  .compile();

// 高考模式: 6 维(content / structure / expression / depth / novelty / formatting 并行)
export const gaokaoGraph = new StateGraph(EssayState)
  .addNode(NODE_NAMES.RELEVANCE, check_relevance)
  .addNode(NODE_NAMES.FAN_OUT, fanOut)
  .addNode(NODE_NAMES.CONTENT, check_content)
  .addNode(NODE_NAMES.STRUCTURE, check_structure)
  .addNode(NODE_NAMES.EXPRESSION, check_expression)
  .addNode(NODE_NAMES.DEPTH, check_depth)
  .addNode(NODE_NAMES.NOVELTY, check_novelty)
  .addNode(NODE_NAMES.FORMATTING, check_formatting)
  .addNode(NODE_NAMES.CALCULATE, calculate_final_score)
  .addEdge(START, NODE_NAMES.RELEVANCE)
  .addConditionalEdges(NODE_NAMES.RELEVANCE, routeRelevance, {
    fan_out: NODE_NAMES.FAN_OUT,
    calculate_final_score: NODE_NAMES.CALCULATE,
  })
  .addEdge(NODE_NAMES.FAN_OUT, NODE_NAMES.CONTENT)
  .addEdge(NODE_NAMES.FAN_OUT, NODE_NAMES.STRUCTURE)
  .addEdge(NODE_NAMES.FAN_OUT, NODE_NAMES.EXPRESSION)
  .addEdge(NODE_NAMES.FAN_OUT, NODE_NAMES.DEPTH)
  .addEdge(NODE_NAMES.FAN_OUT, NODE_NAMES.NOVELTY)
  .addEdge(NODE_NAMES.FAN_OUT, NODE_NAMES.FORMATTING)
  .addEdge(NODE_NAMES.CONTENT, NODE_NAMES.CALCULATE)
  .addEdge(NODE_NAMES.STRUCTURE, NODE_NAMES.CALCULATE)
  .addEdge(NODE_NAMES.EXPRESSION, NODE_NAMES.CALCULATE)
  .addEdge(NODE_NAMES.DEPTH, NODE_NAMES.CALCULATE)
  .addEdge(NODE_NAMES.NOVELTY, NODE_NAMES.CALCULATE)
  .addEdge(NODE_NAMES.FORMATTING, NODE_NAMES.CALCULATE)
  .addEdge(NODE_NAMES.CALCULATE, END)
  .compile();

export function getGraph(mode: Mode) {
  return mode === "gaokao" ? gaokaoGraph : standardGraph;
}

// 向后兼容: 旧代码用 `graph` 导入时默认给 standard
export const graph = standardGraph;
```

- [ ] **Step 3: 类型检查**

Run: `npx tsc --noEmit`
Expected: 0 错误

- [ ] **Step 4: 跑全量单测**

Run: `npm test`
Expected: 所有原有测试 + 5 (mode-storage) + 8 (dimensions) 全部通过

- [ ] **Step 5: Lint**

Run: `npm run lint`
Expected: 0 错误

- [ ] **Step 6: 提交**

```bash
git add src/workflow/state.ts src/workflow/graph.ts
git commit -m "feat(workflow): 编译 standard/gaokao 双 graph,getGraph(mode) 路由"
```

---

## Task 8: useGradingStream 接收 mode

**Files:**
- Modify: `src/hooks/useGradingStream.ts`

- [ ] **Step 1: 替换 useGradingStream.ts**

`src/hooks/useGradingStream.ts` 完整内容:

```ts
import { useCallback, useState } from "react";
import { getGraph } from "../workflow/graph";
import type { EssayStateType } from "../workflow/state";
import type { Mode } from "../lib/mode-storage";

export type StreamEvent = {
  node: string;
  update: Record<string, unknown>;
};

type RunInput = Pick<EssayStateType, "topic" | "essay"> & { mode: Mode };

export function useGradingStream() {
  const [events, setEvents] = useState<StreamEvent[]>([]);
  const [done, setDone] = useState(false);
  const [running, setRunning] = useState(false);

  const reset = useCallback(() => {
    setEvents([]);
    setDone(false);
    setRunning(false);
  }, []);

  const run = useCallback(async ({ mode, topic, essay }: RunInput) => {
    reset();
    setRunning(true);
    try {
      const stream = await getGraph(mode).stream(
        { topic, essay, _mode: mode } as unknown as EssayStateType,
        { streamMode: "updates" },
      );
      for await (const event of stream) {
        for (const [node, update] of Object.entries(event)) {
          setEvents((prev) => [...prev, { node, update: update as Record<string, unknown> }]);
        }
      }
    } finally {
      setDone(true);
      setRunning(false);
    }
  }, [reset]);

  return { events, done, running, run, reset };
}
```

- [ ] **Step 2: 类型检查**

Run: `npx tsc --noEmit`
Expected: 0 错误

- [ ] **Step 3: 跑测试**

Run: `npm test`
Expected: 原 GradingPage 测试失败 — `run` 签名变了,调用处需要补 `mode`。Task 12 修复。

- [ ] **Step 4: 提交**

```bash
git add src/hooks/useGradingStream.ts
git commit -m "feat(hook): useGradingStream.run 接收 mode,按 mode 选 graph"
```

---

## Task 9: ModeToggle 组件

**Files:**
- Create: `src/components/ModeToggle.tsx`

- [ ] **Step 1: 实现 ModeToggle.tsx**

`src/components/ModeToggle.tsx` 完整内容:

```tsx
import type { Mode } from "../lib/mode-storage";

type Props = {
  mode: Mode;
  onChange: (mode: Mode) => void;
  disabled?: boolean;
};

const OPTIONS: { value: Mode; label: string; hint: string }[] = [
  { value: "standard", label: "标准模式", hint: "4 维度" },
  { value: "gaokao", label: "高考模式", hint: "7 维度" },
];

export function ModeToggle({ mode, onChange, disabled = false }: Props) {
  return (
    <div
      className="mode-toggle"
      role="radiogroup"
      aria-label="评分模式"
    >
      <span className="mode-toggle-label">评分模式</span>
      <div className="mode-toggle-pills">
        {OPTIONS.map((opt) => {
          const active = mode === opt.value;
          return (
            <button
              key={opt.value}
              type="button"
              role="radio"
              aria-checked={active}
              className={`mode-toggle-pill ${active ? "active" : ""}`}
              disabled={disabled}
              onClick={() => onChange(opt.value)}
            >
              <span className="mode-toggle-pill-label">{opt.label}</span>
              <span className="mode-toggle-pill-hint">{opt.hint}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
```

- [ ] **Step 2: 类型检查**

Run: `npx tsc --noEmit`
Expected: 0 错误

- [ ] **Step 3: 提交**

```bash
git add src/components/ModeToggle.tsx
git commit -m "feat(ui): 新增 ModeToggle 组件(standard/gaokao segmented)"
```

---

## Task 10: ModeToggle 样式

**Files:**
- Modify: `src/styles/index.css`

- [ ] **Step 1: 在 `index.css` 末尾追加 ModeToggle 样式**

定位:`.form-section` 块的下一个大块(按钮区)之前或合适处。本次追加到 `/* === 表单 === */` 块之后、`/* === 按钮 === */` 块之前(约第 530 行附近)。

实际追加位置:在 `.article-select { ... }` 块结束(`}` 在第 513 行附近)之后,`.char-counter` 之前。

在 `.article-select` 的 `}` 之后插入以下内容(独立一段):

```css
/* ================================================================
   模式切换 — segmented control
   ================================================================ */

.mode-toggle {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 22px;
  padding: 10px 14px;
  background: rgba(255, 252, 244, 0.45);
  border: var(--hairline) solid var(--line);
  border-radius: var(--radius-md);
}

.mode-toggle-label {
  font-family: var(--serif);
  font-size: 12.5px;
  font-weight: 600;
  color: var(--ink-soft);
  letter-spacing: 0.12em;
  flex-shrink: 0;
}

.mode-toggle-label::before {
  content: "";
  display: inline-block;
  width: 3px;
  height: 12px;
  background: var(--vermillion);
  border-radius: 1px;
  margin-right: 8px;
  vertical-align: -1px;
}

.mode-toggle-pills {
  display: flex;
  gap: 0;
  background: var(--paper-2);
  border: var(--hairline) solid var(--line-soft);
  border-radius: var(--radius-sm);
  padding: 3px;
  position: relative;
  flex: 1;
}

.mode-toggle-pill {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 2px;
  padding: 8px 12px;
  background: transparent;
  border: none;
  border-radius: 2px;
  cursor: pointer;
  font-family: var(--serif);
  color: var(--ash);
  transition: color var(--duration) var(--ease), background var(--duration) var(--ease);
  position: relative;
}

.mode-toggle-pill:hover:not(:disabled):not(.active) {
  color: var(--ink-soft);
  background: rgba(184, 54, 43, 0.04);
}

.mode-toggle-pill.active {
  background: var(--paper);
  color: var(--vermillion);
  box-shadow: var(--shadow-sm);
}

.mode-toggle-pill.active::after {
  content: "";
  position: absolute;
  left: 20%;
  right: 20%;
  bottom: 4px;
  height: 2px;
  background: var(--vermillion);
  border-radius: 1px;
}

.mode-toggle-pill:disabled {
  cursor: not-allowed;
  opacity: 0.5;
}

.mode-toggle-pill-label {
  font-size: 13.5px;
  font-weight: 600;
  letter-spacing: 0.08em;
}

.mode-toggle-pill-hint {
  font-family: var(--number);
  font-size: 10.5px;
  color: var(--ash-2);
  letter-spacing: 0.04em;
  font-variant-numeric: tabular-nums;
}

.mode-toggle-pill.active .mode-toggle-pill-hint {
  color: var(--vermillion);
  opacity: 0.7;
}

@media (max-width: 540px) {
  .mode-toggle {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
  .mode-toggle-pills {
    width: 100%;
  }
}
```

- [ ] **Step 2: 跑 lint**

Run: `npm run lint`
Expected: 0 错误

- [ ] **Step 3: 提交**

```bash
git add src/styles/index.css
git commit -m "style(ui): ModeToggle segmented 控件样式(宣纸 + 朱砂)"
```

---

## Task 11: FormSection 接入 ModeToggle

**Files:**
- Modify: `src/components/FormSection.tsx`

- [ ] **Step 1: 替换 FormSection.tsx**

`src/components/FormSection.tsx` 完整内容:

```tsx
import { useState, type FormEvent } from "react";
import { ARTICLES } from "../lib/articles";
import { ModeToggle } from "./ModeToggle";
import type { Mode } from "../lib/mode-storage";

type Props = {
  disabled: boolean;
  onSubmit: (topic: string, essay: string) => void;
  quotaExhausted?: boolean;
  mode: Mode;
  onModeChange: (mode: Mode) => void;
};

export function FormSection({
  disabled,
  onSubmit,
  quotaExhausted = false,
  mode,
  onModeChange,
}: Props) {
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
      <ModeToggle mode={mode} onChange={onModeChange} disabled={disabled} />
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
        <span className="char-counter" aria-live="polite">
          <strong>{essay.length}</strong> 字
        </span>
      </div>
      <button
        type="submit"
        className="btn-submit"
        disabled={disabled || quotaExhausted}
        title={quotaExhausted ? "免费次数已用完,清空浏览器数据可重置" : undefined}
      >
        {quotaExhausted ? "次数已用完" : disabled ? "评分中" : "开始评分"}
      </button>
    </form>
  );
}
```

- [ ] **Step 2: 类型检查**

Run: `npx tsc --noEmit`
Expected: GradingPage 报错 — FormSection 缺 `mode` / `onModeChange` props。Task 12 修复。

- [ ] **Step 3: 提交**

```bash
git add src/components/FormSection.tsx
git commit -m "refactor(form): FormSection 接入 ModeToggle"
```

---

## Task 12: GradingPage 接入 mode

**Files:**
- Modify: `src/pages/GradingPage.tsx`

- [ ] **Step 1: 替换 GradingPage.tsx**

`src/pages/GradingPage.tsx` 完整内容:

```tsx
import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Header } from "../components/Header";
import { FormSection } from "../components/FormSection";
import { LoadingBar } from "../components/LoadingBar";
import { ScoreCard } from "../components/ScoreCard";
import { SkeletonCard } from "../components/SkeletonCard";
import { FinalScoreCard } from "../components/FinalScoreCard";
import { useGradingStream } from "../hooks/useGradingStream";
import { useQuota } from "../hooks/useQuota";
import { loadSettings } from "../lib/settings";
import type { ScoreDetail } from "../workflow/state";
import { NODE_NAMES } from "../workflow/config";
import { QUOTA_LIMIT } from "../hooks/useQuota";
import { getDimensions, getLabel } from "../workflow/dimensions";
import { loadMode, saveMode, type Mode } from "../lib/mode-storage";

const LOADING_TEXTS: Record<string, string> = {
  [NODE_NAMES.RELEVANCE]: "智能体正在审题...",
  [NODE_NAMES.FAN_OUT]: "审题完成，正在启动多维度并行评分...",
  [NODE_NAMES.EVIDENCE]: "正在分析论据...",
  [NODE_NAMES.STRUCTURE]: "正在评估结构...",
  [NODE_NAMES.EXPRESSION]: "正在鉴赏语言...",
  [NODE_NAMES.CONTENT]: "正在分析内容与论据...",
  [NODE_NAMES.DEPTH]: "正在评估思想深度...",
  [NODE_NAMES.NOVELTY]: "正在评估创新创意...",
  [NODE_NAMES.FORMATTING]: "正在检查卷面格式...",
  [NODE_NAMES.CALCULATE]: "正在计算综合评分...",
};

const GAOKAO_PARALLEL = [
  NODE_NAMES.CONTENT,
  NODE_NAMES.STRUCTURE,
  NODE_NAMES.EXPRESSION,
  NODE_NAMES.DEPTH,
  NODE_NAMES.NOVELTY,
  NODE_NAMES.FORMATTING,
] as const;

const STANDARD_PARALLEL = [
  NODE_NAMES.EVIDENCE,
  NODE_NAMES.STRUCTURE,
  NODE_NAMES.EXPRESSION,
] as const;

function extractScoreDetail(node: string, update: Record<string, unknown>): ScoreDetail | null {
  const key = node.replace("check_", "");
  const detail = (update as Record<string, unknown>)[key] ?? update[node];
  if (
    detail &&
    typeof detail === "object" &&
    "score" in detail &&
    "reason" in detail &&
    typeof (detail as ScoreDetail).score === "number"
  ) {
    return detail as ScoreDetail;
  }
  return null;
}

export function GradingPage() {
  const navigate = useNavigate();
  const { events, done, running, run, reset } = useGradingStream();
  const { used, exhausted, increment } = useQuota();
  const [mode, setMode] = useState<Mode>(() => loadMode());

  useEffect(() => {
    if (!loadSettings().apiKey) navigate("/settings", { replace: true });
  }, [navigate]);

  useEffect(() => {
    saveMode(mode);
    reset();
  }, [mode, reset]);

  const latestLoadingText = useMemo(() => {
    for (let i = events.length - 1; i >= 0; i--) {
      const text = LOADING_TEXTS[events[i].node];
      if (text) return text;
    }
    return LOADING_TEXTS[NODE_NAMES.RELEVANCE];
  }, [events]);

  const relevanceEvent = events.find((e) => e.node === NODE_NAMES.RELEVANCE);
  const finalScoreUpdate = events.find((e) => e.node === NODE_NAMES.CALCULATE)?.update as
    | { final_score?: number }
    | undefined;

  const parallelDims = mode === "gaokao" ? GAOKAO_PARALLEL : STANDARD_PARALLEL;

  function handleModeChange(next: Mode) {
    if (running) return;
    setMode(next);
  }

  function handleSubmit(topic: string, essay: string) {
    if (exhausted) return;
    increment();
    run({ mode, topic, essay }).catch((err) => alert(`评分请求失败: ${err.message ?? err}`));
  }

  const showResults = events.length > 0;

  let dimensionIndex = 0;
  const nextIndex = () => ++dimensionIndex;

  return (
    <div className="container">
      <Header
        title="作文评分智能体"
        subtitle="基于 LangGraph 的多维度智能评分"
        quota={exhausted ? `已达上限(${QUOTA_LIMIT}/${QUOTA_LIMIT})` : `已用 ${used}/${QUOTA_LIMIT}`}
        quotaExhausted={exhausted}
      />

      <FormSection
        disabled={running}
        onSubmit={handleSubmit}
        quotaExhausted={exhausted}
        mode={mode}
        onModeChange={handleModeChange}
      />
      <LoadingBar visible={running} text={done ? "评分完成" : latestLoadingText} />

      <div className={`results-section ${showResults ? "active" : ""}`}>
        {showResults && (
          <h2 className="section-title">
            <span>{mode === "gaokao" ? "高考模式 · 多维度评分" : "多维度评分"}</span>
            <small>{mode === "gaokao" ? "GAOKAO MODE" : "DIMENSIONAL ANALYSIS"}</small>
          </h2>
        )}
        <div className="score-grid">
          {relevanceEvent && (() => {
            const d = extractScoreDetail(NODE_NAMES.RELEVANCE, relevanceEvent.update);
            return d ? (
              <ScoreCard
                title={getLabel(NODE_NAMES.RELEVANCE)}
                detail={d}
                index={nextIndex()}
              />
            ) : null;
          })()}

          {parallelDims.map((dim) => {
            const event = events.find((e) => e.node === dim);
            if (event) {
              const d = extractScoreDetail(dim, event.update);
              if (d) return <ScoreCard key={dim} title={getLabel(dim)} detail={d} index={nextIndex()} />;
            }
            return relevanceEvent ? <SkeletonCard key={dim} /> : null;
          })}

          {finalScoreUpdate?.final_score !== undefined && (
            <FinalScoreCard score={finalScoreUpdate.final_score} visible={done} />
          )}
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: 类型检查**

Run: `npx tsc --noEmit`
Expected: 0 错误

- [ ] **Step 3: 跑测试**

Run: `npm test`
Expected: 现有 GradingPage 测试失败(签名变了)。Task 13 修复。

- [ ] **Step 4: 提交**

```bash
git add src/pages/GradingPage.tsx
git commit -m "feat(page): GradingPage 接入 mode state、持久化、ModeToggle 联动"
```

---

## Task 13: 集成测试 — mode 切换与持久化

**Files:**
- Modify: `tests/pages/GradingPage.test.tsx`

- [ ] **Step 1: 替换测试文件**

`tests/pages/GradingPage.test.tsx` 完整内容:

```tsx
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";

// 跟踪 getGraph(mode).stream 的调用,验证 mode 路由
const streamMock = vi.fn();

vi.mock("../../src/workflow/graph", () => {
  return {
    graph: { stream: () => (async function* () {})() },
    standardGraph: { stream: () => (async function* () {})() },
    gaokaoGraph: { stream: () => (async function* () {})() },
    getGraph: (mode: "standard" | "gaokao") => ({
      stream: (state: unknown) => {
        streamMock({ mode, state });
        return (async function* () {
          yield { check_relevance: { relevance: { score: 0.9, reason: "good" } } };
        })();
      },
    }),
  };
});

import { GradingPage } from "../../src/pages/GradingPage";

function renderGradingPage() {
  return render(
    <MemoryRouter>
      <GradingPage />
    </MemoryRouter>
  );
}

function fillAndSubmit() {
  fireEvent.change(screen.getByLabelText("作文题目"), { target: { value: "我的题目" } });
  fireEvent.change(screen.getByLabelText("作文内容"), { target: { value: "我的作文内容" } });
  const form = document.querySelector("form.form-section")!;
  fireEvent.submit(form);
}

describe("GradingPage 配额集成", () => {
  beforeEach(() => {
    localStorage.clear();
    streamMock.mockClear();
  });

  it("配额未用尽时:点提交触发 graph.stream 并增加 used", async () => {
    localStorage.setItem("grading-quota-v1", JSON.stringify({ used: 0 }));

    renderGradingPage();

    fillAndSubmit();

    await waitFor(() => expect(streamMock).toHaveBeenCalled());

    expect(JSON.parse(localStorage.getItem("grading-quota-v1") ?? "{}")).toEqual({ used: 1 });
  });

  it("配额用尽时:即使提交表单,graph.stream 也不会被调用 (C1 修复)", async () => {
    localStorage.setItem("grading-quota-v1", JSON.stringify({ used: 10 }));

    renderGradingPage();

    const btn = screen.getByRole("button", { name: /次数已用完/ }) as HTMLButtonElement;
    expect(btn.disabled).toBe(true);

    fillAndSubmit();

    await new Promise((r) => setTimeout(r, 50));

    expect(streamMock).not.toHaveBeenCalled();
    expect(JSON.parse(localStorage.getItem("grading-quota-v1") ?? "{}")).toEqual({ used: 10 });
  });
});

describe("GradingPage 模式集成", () => {
  beforeEach(() => {
    localStorage.clear();
    streamMock.mockClear();
  });

  it("默认 mode = gaokao", () => {
    renderGradingPage();
    const gaokaoBtn = screen.getByRole("radio", { name: /高考模式/ }) as HTMLButtonElement;
    expect(gaokaoBtn.getAttribute("aria-checked")).toBe("true");
  });

  it("点「标准模式」后下次 run 调用 standardGraph (getGraph 收到 standard)", async () => {
    localStorage.setItem("grading-quota-v1", JSON.stringify({ used: 0 }));
    renderGradingPage();

    fireEvent.click(screen.getByRole("radio", { name: /标准模式/ }));

    fillAndSubmit();

    await waitFor(() => expect(streamMock).toHaveBeenCalled());
    const call = streamMock.mock.calls[0][0];
    expect(call.mode).toBe("standard");
  });

  it("高考模式下 run 调用 getGraph(gaokao)", async () => {
    localStorage.setItem("grading-quota-v1", JSON.stringify({ used: 0 }));
    renderGradingPage();

    fillAndSubmit();

    await waitFor(() => expect(streamMock).toHaveBeenCalled());
    const call = streamMock.mock.calls[0][0];
    expect(call.mode).toBe("gaokao");
  });

  it("模式选择写入 localStorage", () => {
    renderGradingPage();

    fireEvent.click(screen.getByRole("radio", { name: /标准模式/ }));

    expect(localStorage.getItem("grading-mode-v1")).toBe(JSON.stringify("standard"));
  });

  it("已保存的 mode 加载时高亮对应按钮", () => {
    localStorage.setItem("grading-mode-v1", JSON.stringify("standard"));
    renderGradingPage();

    const standardBtn = screen.getByRole("radio", { name: /标准模式/ }) as HTMLButtonElement;
    const gaokaoBtn = screen.getByRole("radio", { name: /高考模式/ }) as HTMLButtonElement;
    expect(standardBtn.getAttribute("aria-checked")).toBe("true");
    expect(gaokaoBtn.getAttribute("aria-checked")).toBe("false");
  });
});
```

- [ ] **Step 2: 跑测试**

Run: `npx vitest run tests/pages/GradingPage.test.tsx`
Expected: 7 passed(2 配额 + 5 模式)

- [ ] **Step 3: 跑全量测试**

Run: `npm test`
Expected: 全部通过

- [ ] **Step 4: Lint**

Run: `npm run lint`
Expected: 0 错误

- [ ] **Step 5: 提交**

```bash
git add tests/pages/GradingPage.test.tsx
git commit -m "test(page): 新增 mode 切换/持久化/默认的集成测试"
```

---

## Task 14: 更新 CHANGELOG 与 README

**Files:**
- Modify: `CHANGELOG.md`
- Modify: `README.md`

- [ ] **Step 1: 在 `CHANGELOG.md` 顶部 `[Unreleased]` 下追加**

在 `### Added` 段(若有)或新加 `### Added` 段(若没有)写入:

```markdown
### Added
- 高考作文模式:首页 FormSection 顶部新增「标准模式 / 高考模式」切换按钮;开启后评分工作流从 4 维度升级为 7 维度(审题立意 / 内容论据 / 篇章结构 / 语言文采 / 思想深度 / 创新创意 / 卷面格式),全面对齐 `w.md` 的「基础等级 + 发展等级 + 扣分细则」;总分仍以 1.00 满分,各维度等权 1/7。系统 prompt 拆为 standard/gaokao 两套,gaokao 套内化 5 等评分 + 16 点特征 + 扣分细则。模式选择持久化于 `localStorage: grading-mode-v1`,默认 `gaokao`。
```

并加:

```markdown
### Changed
- 默认评分模式从「标准模式」改为「高考模式」
```

- [ ] **Step 2: 在 `README.md` 中找到四维度表格,扩展为七维度表**

定位:`### 四维度评分体系` 段。当前 4 行(审题/论据/结构/语言)替换为以下七维度表(同时把标题改为「七维度评分体系(高考模式)」):

```markdown
### 七维度评分体系（高考模式）

| 维度 | 说明 | 权重 |
|------|------|------|
| 审题立意 | 评估是否准确理解题目，主题是否深刻 | 1/7 |
| 内容论据 | 评估内容是否充实、论据是否典型 | 1/7 |
| 篇章结构 | 评估段落安排、层次与过渡衔接 | 1/7 |
| 语言文采 | 评估用词、句式、修辞与文采 | 1/7 |
| 思想深度 | 评估是否透过现象看本质、揭示因果 | 1/7 |
| 创新创意 | 评估见解、构思、推理想象是否独到 | 1/7 |
| 卷面格式 | 评估错别字、标点、字数、标题 | 1/7 |
```

并在「快速开始」与「使用流程」之间加一节:

```markdown
### 评分模式

首页 FormSection 顶部有「标准模式 / 高考模式」切换：

- **标准模式**：4 维度（审题立意 / 论据 / 结构 / 语言文采），权重 0.3 / 0.2 / 0.2 / 0.3
- **高考模式**（默认）：7 维度，对齐教育部考试中心高考作文评分细则（基础 40 + 发展 20 + 卷面）

模式选择自动保存到浏览器，刷新后保持。
```

- [ ] **Step 3: 验证 README 渲染(Markdown lint 或 git diff)**

Run: `git diff README.md | head -60`
Expected: 看到上面的新段落

- [ ] **Step 4: 提交**

```bash
git add CHANGELOG.md README.md
git commit -m "docs: README/CHANGELOG 记录高考模式与 7 维度"
```

---

## Task 15: 端到端验证

**Files:** (无)

- [ ] **Step 1: 跑全套质量门禁**

```bash
npx tsc --noEmit
npm run lint
npm test
```

Expected: 全部 0 错误 / 全部通过

- [ ] **Step 2: 跑 build**

Run: `npm run build`
Expected: 成功产出 `dist/`

- [ ] **Step 3: 手动验证(Markdown checklist,无需截图)**

启动 `npm run dev`,在浏览器中检查:

- [ ] 页面打开时,FormSection 顶部「高考模式」高亮(朱砂红)
- [ ] 切到「标准模式」,再切回「高考模式」,刷新页面后保留最后一次选择
- [ ] 高考模式提交作文,渲染 7 张评分卡(每张标题对应维度名)
- [ ] 标准模式提交作文,渲染 4 张评分卡(行为不变)
- [ ] FinalScoreCard 仍显示「满分 1.00」,两种模式文案一致
- [ ] 跑题作文(relevance ≤ 0.5)两种模式都直接出综合分,无维度卡
- [ ] 评分中切换按钮被置灰

- [ ] **Step 4: 写验收 commit**

```bash
git commit --allow-empty -m "chore: 高考模式 7 维度端到端验收通过"
```

(若 Step 1/2/3 全部完成,可以空 commit 作为里程碑;若有未完成项,先 fix 再 commit)

---

## 自审记录

**Spec 覆盖**:

| Spec 章节 | 实现于 |
| --- | --- |
| 1 背景与动机 | README/CHANGELOG(Task 14) |
| 2 架构(双 graph / state 扩展 / mode 路由) | Task 3, 6, 7, 8 |
| 3 7 维度拆解 | Task 2(dimensions.ts) |
| 4.1 文件清单 | Task 1–12 |
| 4.2 数据流 | Task 11, 12 |
| 4.3 UI 视觉 | Task 9, 10 |
| 5.1 错误处理 | Task 1(mode-storage 兜底) |
| 5.2 测试 | Task 1, 2, 13 |
| 5.3 迁移 / 影响面 | Task 3(权重迁移)、14(README/CHANGELOG) |
| 5.4 YAGNI | Plan 范围内未引入 |
| 6 验收清单 | Task 15 |

**类型一致性检查**:

- `Mode` 类型: `src/lib/mode-storage.ts` 导出,`dimensions.ts` / `prompts.ts` / `nodes.ts` / `graph.ts` / `useGradingStream.ts` / `FormSection.tsx` / `GradingPage.tsx` 一致使用
- `EssayState._mode`: `state.ts` 字段名,`useGradingStream.run` 入参 `_mode: mode` (Task 8),`nodes.ts` 读取 `state._mode ?? "standard"` (Task 6)
- `getDimensions(mode)` 返回 `readonly Dim[]`,`getWeights(mode)` 返回 `Map<string, number>` (Task 2)
- `NODE_NAMES.CONTENT/DEPTH/NOVELTY/FORMATTING` (Task 3) 与 `nodes.ts` 中 `check_content/check_depth/check_novelty/check_formatting` (Task 6) 字符串一致
- `getLabel(node)` (Task 2) 与 GradingPage (Task 12) 调用一致

**无占位符**: 已检查 — 所有代码块完整,所有命令明确。
