# 会话级评分配额限制设计

> 每个浏览器（localStorage 维度）累计只能使用「开始评分」10 次。

## 背景与目标

- 当前项目部署在 GitHub Pages，前端直连 LLM Provider，API Key 由用户在设置页配置
- README 已明确建议用户「在 LLM provider 端设置月度额度上限」，但默认填了演示 Key，对 Key 所属账户构成盗刷风险
- 需要一道客户端轻量防线，**降低**（不是消除）默认 Key 被刷量的风险
- 用户已确认：localStorage 持久化、配额耗尽禁用按钮、UI 持续展示「已用 X/10」

## 非目标（YAGNI）

- 不做服务端配额校验（项目是纯前端 SPA，无后端）
- 不做账号体系 / 设备指纹 / IP 限流
- 不监听 `storage` event 做多标签实时同步
- 不预留 `firstUsedAt` 时间戳字段（以后要按时间重置再加）
- 用完后不引导跳转设置页

## 架构

```
┌─────────────────────────────────────────────────────────┐
│ GradingPage                                              │
│  const { used, remaining, exhausted, increment } = ...   │
│                                                          │
│  <Header title=... subtitle=... quota="已用 X/10" />    │
│                                                          │
│  <FormSection                                            │
│    disabled={running || exhausted}                      │
│    onSubmit={(t, e) => { increment(); run(...) }}       │
│  />                                                     │
└────────┬────────────────────────────┬───────────────────┘
         │                            │
         ▼                            ▼
   src/hooks/useQuota.ts        src/lib/quota.ts
   (useState + localStorage)    (loadQuota / incrementQuota / QUOTA_LIMIT)
         │                            │
         └────────► localStorage ◄────┘
                   键: grading-quota-v1
                   值: { "used": 3 }
```

## 数据契约

### `src/lib/quota.ts`

```ts
const STORAGE_KEY = "grading-quota-v1";
const MAX_USES = 10;

export type QuotaState = { used: number };

export const QUOTA_LIMIT = MAX_USES;

export function loadQuota(): QuotaState;
export function saveQuota(state: QuotaState): void;
export function incrementQuota(): QuotaState;
```

**`loadQuota` 修正规则**（按顺序）：

| 输入 | 输出 |
| :--- | :--- |
| 空 / 无键 | `{ used: 0 }` |
| JSON 损坏 | `{ used: 0 }` |
| `used` 非数字 / `NaN` | `{ used: 0 }` |
| `used < 0` | `{ used: 0 }` |
| `used` 小数 | `{ used: Math.floor(used) }` |
| `used > MAX` | `{ used: MAX }` |
| 正常 `0..MAX` 整数 | 原值 |

**`incrementQuota` 行为**：

- 读 → `used = min(used + 1, MAX)` → 写 → 返回新 state
- `setItem` 抛错时：`console.warn` 后返回原 state（**不递增**）

### `src/hooks/useQuota.ts`

```ts
type UseQuotaResult = {
  used: number;          // 当前已用次数
  remaining: number;     // QUOTA_LIMIT - used, 不会为负
  exhausted: boolean;    // used >= QUOTA_LIMIT
  increment: () => void; // 写 localStorage 并更新 state
};

export function useQuota(): UseQuotaResult;
```

实现要点：

- `useState(() => loadQuota())` 初始惰性求值
- `increment` 用 `useCallback` 包裹
- 不订阅 `storage` event

## UI 行为

### `Header` 组件

- 新增 `quota?: string` prop，可选展示
- 用完时调用方传入 `"已达上限(10/10)"`，未用完传入 `"已用 X/10"`
- 用完态样式：朱砂红 `#b94a48`（与项目现有警示色一致）
- 现有 `{ title, subtitle }` 调用方不受影响

### `FormSection` 组件

- 新增 `quotaExhausted?: boolean` prop
- 当 `quotaExhausted === true`：
  - 提交按钮 `disabled`、`cursor: not-allowed`、文案改为「次数已用完」
  - 按钮 `title="免费次数已用完，清空浏览器数据可重置"`（原生 tooltip，不引第三方）
  - 输入框不禁用（用户仍可阅读/复制历史输入）

### `GradingPage` 集成

- `handleSubmit` 顺序：**先 `increment()`，再 `run()`**
- `disabled` 条件：`running || quotaExhausted`
- 「次数已用完」时 `run` 不被调用，配额不再增加

## 错误处理

| 场景 | 行为 |
| :--- | :--- |
| localStorage 不可用（隐私模式 / 配额耗尽） | `loadQuota` 返 0；`incrementQuota` 写失败静默 + `console.warn` |
| JSON 损坏 | `loadQuota` 返 0 |
| 手改 `used: 15` | 截断为 10 |
| 手改 `used: -1` | 修正为 0 |
| 多标签同时打开各 +1 | 退化：略超 10，可接受 |
| 连点开始评分 | `running` 置 true 后挡住后续点击，边界可接受 |

## 测试

### `tests/lib/quota.test.ts`（镜像 `tests/workflow/settings.test.ts`）

1. `loadQuota` 返 0 当 storage 为空
2. `loadQuota` 返 0 当 JSON 损坏
3. `loadQuota` 正常解析 `{"used": 3}`
4. `loadQuota` 修正 `used: -1` → 0
5. `loadQuota` 修正 `used: 15` → 10
6. `loadQuota` 修正 `used: 3.7` → 3
7. `loadQuota` 修正 `used: "abc"` → 0
8. `incrementQuota` 从 0 到 1
9. `incrementQuota` 从 9 到 10（到上限仍 +1）
10. `incrementQuota` 从 10 再 +1 仍返 10
11. `incrementQuota` 写失败时不递增，返回原 state
12. `saveQuota` + `loadQuota` 往返一致

### `tests/hooks/useQuota.test.ts`（镜像 `useGradingStream.test.ts`）

1. 初次渲染：`used: 0`、`remaining: 10`、`exhausted: false`
2. `increment()` 后 `used` 增 1
3. `increment()` 后 localStorage 写入正确
4. `used === 10` 时 `exhausted: true`、`remaining: 0`
5. 多次 `increment()` 累加正确

### 手动验收（不在自动化里）

- `npm run dev`，连点 10 次「开始评分」，第 11 次按钮置灰且 hover 显示 tooltip
- devtools → Application → Local Storage，看到 `grading-quota-v1 = {"used":10}`
- 手动改 `localStorage.used = 5` 刷新，按钮恢复可点
- 隐私模式打开，`loadQuota` 返 0（配额限制失效，符合降级）

## 文件改动清单

| 文件 | 改动 |
| :--- | :--- |
| `src/lib/quota.ts` | 新增 |
| `src/hooks/useQuota.ts` | 新增 |
| `src/components/Header.tsx` | 新增 `quota?: string` prop |
| `src/components/FormSection.tsx` | 新增 `quotaExhausted?: boolean` prop |
| `src/pages/GradingPage.tsx` | 接入 `useQuota`，传入 Header / FormSection |
| `tests/lib/quota.test.ts` | 新增 |
| `tests/hooks/useQuota.test.ts` | 新增 |
| `README.md` | 「安全提示」段加一条「额度限制」说明 |
| `CHANGELOG.md` | `[Unreleased]` 段记录本次新增 |

## 质量门禁

按 `CLAUDE.md` 强制执行：

- `npx tsc --noEmit`
- `npm run lint`
- `npm test`
