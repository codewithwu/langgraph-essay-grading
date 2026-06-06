# Session Quota Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 每个浏览器 localStorage 维度下「开始评分」按钮累计最多使用 10 次,达到上限后禁用按钮并显示提示。

**Architecture:** 新增 `src/lib/quota.ts`(localStorage 读写 + 修正规则)与 `src/hooks/useQuota.ts`(React state 包装)。`GradingPage` 集成,`Header` 加 `quota` 字符串 prop,`FormSection` 加 `quotaExhausted` 布尔 prop。

**Tech Stack:** TypeScript 5.5、React 18、Vitest 2、jsdom

**Spec:** `docs/superpowers/specs/2026-06-06-session-quota-design.md`

---

## File Structure

| 文件 | 状态 | 职责 |
| :--- | :--- | :--- |
| `src/lib/quota.ts` | 新增 | localStorage 读写 + 修正规则 + `incrementQuota` |
| `src/hooks/useQuota.ts` | 新增 | `useState` 包装,暴露 `used`/`remaining`/`exhausted`/`increment` |
| `src/components/Header.tsx` | 修改 | 新增 `quota?: string` 可选 prop |
| `src/components/FormSection.tsx` | 修改 | 新增 `quotaExhausted?: boolean` 可选 prop |
| `src/pages/GradingPage.tsx` | 修改 | 接入 `useQuota`,先 `increment` 再 `run`,传入 Header/FormSection |
| `tests/lib/quota.test.ts` | 新增 | `quota.ts` 单元测试 |
| `tests/hooks/useQuota.test.ts` | 新增 | `useQuota` hook 单元测试 |
| `README.md` | 修改 | 「安全提示」段加一条「额度限制」说明 |
| `CHANGELOG.md` | 修改 | `[Unreleased]` 段记录本次新增 |

---

## Task 1: `src/lib/quota.ts` — 数据访问层(TDD)

**Files:**
- Create: `src/lib/quota.ts`
- Create: `tests/lib/quota.test.ts`

- [ ] **Step 1: 写失败测试**

写入 `tests/lib/quota.test.ts`:

```ts
import { describe, it, expect, beforeEach, vi } from "vitest";
import { loadQuota, saveQuota, incrementQuota, QUOTA_LIMIT, type QuotaState } from "../../src/lib/quota";

describe("quota", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.restoreAllMocks();
  });

  describe("loadQuota", () => {
    it("returns { used: 0 } when storage is empty", () => {
      expect(loadQuota()).toEqual({ used: 0 });
    });

    it("returns { used: 0 } when JSON is corrupt", () => {
      localStorage.setItem("grading-quota-v1", "{not valid");
      expect(loadQuota()).toEqual({ used: 0 });
    });

    it("parses normal { used: 3 }", () => {
      localStorage.setItem("grading-quota-v1", JSON.stringify({ used: 3 }));
      expect(loadQuota()).toEqual({ used: 3 });
    });

    it("corrects negative used to 0", () => {
      localStorage.setItem("grading-quota-v1", JSON.stringify({ used: -1 }));
      expect(loadQuota()).toEqual({ used: 0 });
    });

    it("clamps used above QUOTA_LIMIT to QUOTA_LIMIT", () => {
      localStorage.setItem("grading-quota-v1", JSON.stringify({ used: 15 }));
      expect(loadQuota().used).toBe(QUOTA_LIMIT);
    });

    it("floors fractional used", () => {
      localStorage.setItem("grading-quota-v1", JSON.stringify({ used: 3.7 }));
      expect(loadQuota()).toEqual({ used: 3 });
    });

    it("corrects non-numeric used to 0", () => {
      localStorage.setItem("grading-quota-v1", JSON.stringify({ used: "abc" }));
      expect(loadQuota()).toEqual({ used: 0 });
    });
  });

  describe("saveQuota + loadQuota round-trip", () => {
    it("round-trips through save and load", () => {
      const s: QuotaState = { used: 5 };
      saveQuota(s);
      expect(loadQuota()).toEqual(s);
    });
  });

  describe("incrementQuota", () => {
    it("increments from 0 to 1", () => {
      const result = incrementQuota();
      expect(result).toEqual({ used: 1 });
      expect(loadQuota()).toEqual({ used: 1 });
    });

    it("increments from 9 to QUOTA_LIMIT", () => {
      saveQuota({ used: 9 });
      expect(incrementQuota()).toEqual({ used: QUOTA_LIMIT });
    });

    it("does not exceed QUOTA_LIMIT when already at limit", () => {
      saveQuota({ used: QUOTA_LIMIT });
      expect(incrementQuota()).toEqual({ used: QUOTA_LIMIT });
    });

    it("does not increment when storage write fails", () => {
      saveQuota({ used: 3 });
      const spy = vi.spyOn(Storage.prototype, "setItem").mockImplementation(() => {
        throw new Error("quota exceeded");
      });
      const warn = vi.spyOn(console, "warn").mockImplementation(() => {});
      const result = incrementQuota();
      expect(result).toEqual({ used: 3 });
      expect(warn).toHaveBeenCalled();
      spy.mockRestore();
    });
  });
});
```

- [ ] **Step 2: 跑测试确认失败**

Run: `npm test -- tests/lib/quota.test.ts`
Expected: 失败,提示 `Cannot find module '../../src/lib/quota'`。

- [ ] **Step 3: 写最小实现**

写入 `src/lib/quota.ts`:

```ts
const STORAGE_KEY = "grading-quota-v1";
const MAX_USES = 10;

export type QuotaState = { used: number };

export const QUOTA_LIMIT = MAX_USES;

function clampUsed(raw: unknown): number {
  if (typeof raw !== "number" || Number.isNaN(raw)) return 0;
  const floored = Math.floor(raw);
  if (floored < 0) return 0;
  if (floored > MAX_USES) return MAX_USES;
  return floored;
}

export function loadQuota(): QuotaState {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return { used: 0 };
    const parsed = JSON.parse(raw) as { used?: unknown };
    return { used: clampUsed(parsed.used) };
  } catch {
    return { used: 0 };
  }
}

export function saveQuota(state: QuotaState): void {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
}

export function incrementQuota(): QuotaState {
  const current = loadQuota();
  const next: QuotaState = { used: Math.min(current.used + 1, MAX_USES) };
  try {
    saveQuota(next);
  } catch (err) {
    console.warn("quota: failed to persist", err);
    return current;
  }
  return next;
}
```

- [ ] **Step 4: 跑测试确认通过**

Run: `npm test -- tests/lib/quota.test.ts`
Expected: 全部 12 个 case 通过。

- [ ] **Step 5: 跑类型检查 + lint**

Run:
```bash
npx tsc --noEmit
npm run lint
```
Expected: 都通过(无 error)。

- [ ] **Step 6: 提交**

```bash
git add src/lib/quota.ts tests/lib/quota.test.ts
git commit -m "feat(quota): 新增会话级评分配额 localStorage 读写模块"
```

---

## Task 2: `src/hooks/useQuota.ts` — React 包装层(TDD)

**Files:**
- Create: `src/hooks/useQuota.ts`
- Create: `tests/hooks/useQuota.test.ts`

- [ ] **Step 1: 写失败测试**

写入 `tests/hooks/useQuota.test.ts`:

```ts
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
```

- [ ] **Step 2: 跑测试确认失败**

Run: `npm test -- tests/hooks/useQuota.test.ts`
Expected: 失败,提示 `Cannot find module '../../src/hooks/useQuota'`。

- [ ] **Step 3: 写最小实现**

写入 `src/hooks/useQuota.ts`:

```ts
import { useCallback, useState } from "react";
import { incrementQuota as incrementQuotaStorage, loadQuota, QUOTA_LIMIT as MAX } from "../lib/quota";

export { QUOTA_LIMIT } from "../lib/quota";

type UseQuotaResult = {
  used: number;
  remaining: number;
  exhausted: boolean;
  increment: () => void;
};

export function useQuota(): UseQuotaResult {
  const [used, setUsed] = useState<number>(() => loadQuota().used);

  const increment = useCallback(() => {
    const next = incrementQuotaStorage();
    setUsed(next.used);
  }, []);

  const remaining = Math.max(MAX - used, 0);
  const exhausted = used >= MAX;

  return { used, remaining, exhausted, increment };
}
```

- [ ] **Step 4: 跑测试确认通过**

Run: `npm test -- tests/hooks/useQuota.test.ts`
Expected: 全部 5 个 case 通过。

- [ ] **Step 5: 跑质量门禁**

Run:
```bash
npx tsc --noEmit
npm run lint
```
Expected: 都通过。

- [ ] **Step 6: 提交**

```bash
git add src/hooks/useQuota.ts tests/hooks/useQuota.test.ts
git commit -m "feat(quota): 新增 useQuota hook 包装 localStorage 配额"
```

---

## Task 3: `Header.tsx` — 增加 `quota` prop

**Files:**
- Modify: `src/components/Header.tsx:3-5`

- [ ] **Step 1: 改 Header 增加可选 prop**

把第 3-5 行:

```tsx
type Props = { title: string; subtitle: string };

export function Header({ title, subtitle }: Props) {
```

替换为:

```tsx
type Props = { title: string; subtitle: string; quota?: string; quotaExhausted?: boolean };

export function Header({ title, subtitle, quota, quotaExhausted = false }: Props) {
```

- [ ] **Step 2: 在 `</p>` 标签后增加 quota 展示**

在 `Header.tsx` 第 19 行 `</p>` 之后、第 20 行 `<Link>` 之前,插入:

```tsx
        {quota && (
          <span className={quotaExhausted ? "app-header-quota exhausted" : "app-header-quota"}>
            {quota}
          </span>
        )}
```

最终第 17-23 行应类似:

```tsx
        <p className="subtitle">
          {subtitle}
        </p>
        {quota && (
          <span className={quotaExhausted ? "app-header-quota exhausted" : "app-header-quota"}>
            {quota}
          </span>
        )}
      </div>
      <Link to="/settings" className="icon-btn" aria-label="设置">
```

- [ ] **Step 3: 增加对应 CSS 样式**

打开 `src/styles/` 下全局 CSS 文件(定位包含 `.app-header-meta` 的那个),在合适位置追加:

```css
.app-header-quota {
  display: inline-block;
  margin-top: 8px;
  padding: 2px 10px;
  font-size: 13px;
  border-radius: 999px;
  background: rgba(0, 0, 0, 0.06);
  color: #555;
}
.app-header-quota.exhausted {
  background: rgba(185, 74, 72, 0.12);
  color: #b94a48;
}
```

> 注:实际样式文件名以仓库实际为准;若样式表拆成多文件,选择放主全局文件的那个。`exhausted` 类由 `Header` 组件根据 `quotaExhausted` prop 内部追加(见 Task 5 调用方需传入该 prop)。

- [ ] **Step 4: 跑类型检查 + lint**

Run:
```bash
npx tsc --noEmit
npm run lint
```
Expected: 都通过(无 error/warning)。

- [ ] **Step 5: 提交**

```bash
git add src/components/Header.tsx src/styles/
git commit -m "feat(header): 新增可选 quota 字符串 prop 用于展示已用次数"
```

---

## Task 4: `FormSection.tsx` — 增加 `quotaExhausted` prop

**Files:**
- Modify: `src/components/FormSection.tsx:4-9, 72-74`

- [ ] **Step 1: 改 Props 类型**

把第 4-7 行:

```tsx
type Props = {
  disabled: boolean;
  onSubmit: (topic: string, essay: string) => void;
};

export function FormSection({ disabled, onSubmit }: Props) {
```

替换为:

```tsx
type Props = {
  disabled: boolean;
  onSubmit: (topic: string, essay: string) => void;
  quotaExhausted?: boolean;
};

export function FormSection({ disabled, onSubmit, quotaExhausted = false }: Props) {
```

- [ ] **Step 2: 改提交按钮逻辑**

把第 72-74 行:

```tsx
      <button type="submit" className="btn-submit" disabled={disabled}>
        {disabled ? "评分中" : "开始评分"}
      </button>
```

替换为:

```tsx
      <button
        type="submit"
        className="btn-submit"
        disabled={disabled || quotaExhausted}
        title={quotaExhausted ? "免费次数已用完,清空浏览器数据可重置" : undefined}
      >
        {quotaExhausted ? "次数已用完" : disabled ? "评分中" : "开始评分"}
      </button>
```

> 注:`disabled` prop 仍只代表「评分中」(控制输入框和文章下拉的禁用);按钮额外叠加 `quotaExhausted` —— 这样输入框在配额耗尽时仍可阅读/复制历史输入(spec 明确要求)。

- [ ] **Step 3: 跑类型检查 + lint**

Run:
```bash
npx tsc --noEmit
npm run lint
```
Expected: 都通过。

- [ ] **Step 4: 提交**

```bash
git add src/components/FormSection.tsx
git commit -m "feat(form): 新增 quotaExhausted prop,耗尽时禁用并展示 tooltip"
```

---

## Task 5: `GradingPage.tsx` — 接入 useQuota

**Files:**
- Modify: `src/pages/GradingPage.tsx:9-12, 47-49, 68-70, 79, 81`

- [ ] **Step 1: 增加 import**

把第 9-12 行:

```tsx
import { useGradingStream } from "../hooks/useGradingStream";
import { loadSettings } from "../lib/settings";
import type { ScoreDetail } from "../workflow/state";
import { NODE_NAMES } from "../workflow/config";
```

替换为:

```tsx
import { useGradingStream } from "../hooks/useGradingStream";
import { useQuota } from "../hooks/useQuota";
import { loadSettings } from "../lib/settings";
import type { ScoreDetail } from "../workflow/state";
import { NODE_NAMES } from "../workflow/config";
import { QUOTA_LIMIT } from "../hooks/useQuota";
```

- [ ] **Step 2: 在组件内调用 useQuota**

把第 48-49 行:

```tsx
  const navigate = useNavigate();
  const { events, done, running, run } = useGradingStream();
```

替换为:

```tsx
  const navigate = useNavigate();
  const { events, done, running, run } = useGradingStream();
  const { used, exhausted, increment } = useQuota();
```

- [ ] **Step 3: 改 handleSubmit 顺序**

把第 68-70 行:

```tsx
  function handleSubmit(topic: string, essay: string) {
    run({ topic, essay }).catch((err) => alert(`评分请求失败: ${err.message ?? err}`));
  }
```

替换为:

```tsx
  function handleSubmit(topic: string, essay: string) {
    increment();
    run({ topic, essay }).catch((err) => alert(`评分请求失败: ${err.message ?? err}`));
  }
```

- [ ] **Step 4: 计算 quotaText 并传 Header / FormSection**

把第 79 行:

```tsx
      <Header title="高考作文评分系统" subtitle="基于 LangGraph 的多维度智能评分" />
```

替换为:

```tsx
      <Header
        title="高考作文评分系统"
        subtitle="基于 LangGraph 的多维度智能评分"
        quota={exhausted ? `已达上限(${QUOTA_LIMIT}/${QUOTA_LIMIT})` : `已用 ${used}/${QUOTA_LIMIT}`}
        quotaExhausted={exhausted}
      />
```

把第 81 行:

```tsx
      <FormSection disabled={running} onSubmit={handleSubmit} />
```

替换为:

```tsx
      <FormSection disabled={running} onSubmit={handleSubmit} quotaExhausted={exhausted} />
```

- [ ] **Step 5: 跑类型检查 + lint + 测试**

Run:
```bash
npx tsc --noEmit
npm run lint
npm test
```
Expected: 全通过。

- [ ] **Step 6: 提交**

```bash
git add src/pages/GradingPage.tsx
git commit -m "feat(page): 在 GradingPage 接入 useQuota,先 increment 再 run"
```

---

## Task 6: `README.md` — 额度限制说明

**Files:**
- Modify: `README.md`(「安全提示」段)

- [ ] **Step 1: 在「安全提示」段底部追加**

定位到 `README.md` 第 96 行(`.env` 之前),在该段最后一条 `✅` 项之后、`## License` 之前,插入:

```markdown
### 额度限制

- 每个浏览器 localStorage 累计只能使用「开始评分」**10 次**(默认 Key 的轻量防刷措施)
- 达到上限后按钮置灰，鼠标悬浮可见「清空浏览器数据可重置」提示
- 配额限制只是客户端降级提醒，**不是**安全边界；真正的安全靠 provider 端设置月度额度上限
```

- [ ] **Step 2: 提交**

```bash
git add README.md
git commit -m "docs: README 安全提示段新增额度限制说明"
```

---

## Task 7: `CHANGELOG.md` — 记录本次新增

**Files:**
- Modify: `CHANGELOG.md`(在 `[Unreleased]` 段下)

- [ ] **Step 1: 在 `### Added` 下追加**

定位到 `CHANGELOG.md` 第 12 行(`### Added` 标题)下的子项,在最后一条(「体验提升」)之后追加:

```markdown
- **额度限制**: 每个浏览器 localStorage 累计只能使用「开始评分」10 次,达到上限后按钮置灰并提示;通过 `src/lib/quota.ts` + `src/hooks/useQuota.ts` 实现,头/表单区持续显示「已用 X/10」
```

- [ ] **Step 2: 提交**

```bash
git add CHANGELOG.md
git commit -m "docs: CHANGELOG 记录本次会话配额功能"
```

---

## Task 8: 最终质量门禁

- [ ] **Step 1: 全量跑质量门禁**

Run:
```bash
npx tsc --noEmit
npm run lint
npm test
```
Expected: 三项都通过。

- [ ] **Step 2: 全量构建**

Run: `npm run build`
Expected: 成功生成 `dist/`,无 TS 错误。

- [ ] **Step 3: 手动验证(开发模式)**

Run: `npm run dev`
手动验收:
1. 打开页面,头部右侧出现灰色「已用 0/10」徽章
2. 点 1 次「开始评分」,徽章变「已用 1/10」
3. (可选加速验收) 浏览器 console 执行:
   ```js
   localStorage.setItem('grading-quota-v1', JSON.stringify({ used: 9 }));
   location.reload();
   ```
   再点 1 次,徽章变红色「已达上限(10/10)」,按钮置灰且悬浮显示 tooltip

- [ ] **Step 4: 确认所有任务 commit 已落地**

Run: `git log --oneline -10`
Expected: 至少包含 7 条本次新增的 commit(任务 1-7 各一条),均在 main 分支上,无未提交改动。
