# LLM 默认配置外置到 JSON Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 LLM 默认配置（含 API Key）从 `src/lib/settings.ts` 的内联硬编码外置到 `src/config/llm-defaults.json`，使新用户首次访问页面即可直接连通模型，无需手填任何字段。

**Architecture:** 新建 JSON 文件存放三项默认值，`src/lib/settings.ts` 通过 `resolveJsonModule` 静态导入并赋给 `DEFAULT_SETTINGS`。现有 `loadSettings()` 的合并语义不变 → 老用户 localStorage 中的值仍然优先。下游 `getLLM()` / `SettingsPage` / `useGradingStream` 零改动。

**Tech Stack:** TypeScript 5 + Vite 5 + Vitest（已有），无新依赖。

**Spec:** [`docs/superpowers/specs/2026-06-06-llm-defaults-json-design.md`](../specs/2026-06-06-llm-defaults-json-design.md)

---

## File Structure

| 文件 | 操作 | 职责 |
|---|---|---|
| `src/config/llm-defaults.json` | 新建 | 集中存放三项 LLM 默认值；唯一需要修改 Key 时碰的文件 |
| `src/lib/settings.ts` | 修改（约 5 行） | 用 JSON 导入替换内联 `DEFAULT_SETTINGS` 字面量 |
| `tests/workflow/settings.test.ts` | 追加 1 条用例 | 防御 JSON 文件丢失 / 字段改名导致的回归 |
| `CHANGELOG.md` | 追加 1 行 `[Unreleased]` | 记录改动 |
| `README.md` | 修改使用流程 + 追加安全提示 | 告知用户开箱即用 + fork 时必须替换 Key |

---

## Task 1: TDD — JSON 外置默认配置

**Files:**
- Create: `src/config/llm-defaults.json`
- Modify: `src/lib/settings.ts:1-13`
- Test: `tests/workflow/settings.test.ts`（追加 1 条用例，约第 33 行后）

- [ ] **Step 1: 写失败的测试**

打开 `tests/workflow/settings.test.ts`，在最后一条 `it(...)` 之后、`describe` 闭合 `})` 之前，追加如下用例：

```typescript
  it("default settings is loaded from JSON with all fields populated", () => {
    expect(DEFAULT_SETTINGS.apiKey).toMatch(/^sk-/);
    expect(DEFAULT_SETTINGS.baseUrl).toBe("https://api.tbox.cn/api/llm/v1/");
    expect(DEFAULT_SETTINGS.modelName).toBe("Ling-2.6-1T");
  });
```

- [ ] **Step 2: 运行测试，确认失败**

Run: `npx vitest run tests/workflow/settings.test.ts -t "default settings is loaded from JSON"`

Expected: FAIL，断言 `DEFAULT_SETTINGS.apiKey` 不匹配 `/^sk-/`（当前是空字符串 `""`）。

- [ ] **Step 3: 创建 JSON 文件**

新建文件 `src/config/llm-defaults.json`，内容：

```json
{
  "apiKey": "sk-studio-2722acfd3da941e4b2f1326802c5d7d3",
  "baseUrl": "https://api.tbox.cn/api/llm/v1/",
  "modelName": "Ling-2.6-1T"
}
```

注意：字段名必须与 `Settings` 类型完全一致（`apiKey` / `baseUrl` / `modelName`，camelCase）。

- [ ] **Step 4: 修改 settings.ts，用 JSON 导入替换字面量**

打开 `src/lib/settings.ts`，把第 9-13 行：

```typescript
export const DEFAULT_SETTINGS: Settings = {
  apiKey: "",
  baseUrl: "https://api.tbox.cn/api/llm/v1/",
  modelName: "Ling-2.6-1T",
};
```

替换为：

```typescript
import defaults from "../config/llm-defaults.json";

export const DEFAULT_SETTINGS: Settings = defaults;
```

把 `import defaults` 放到文件顶部（第 1 行之前）；最终文件顶部应是：

```typescript
import defaults from "../config/llm-defaults.json";

const STORAGE_KEY = "grading-settings-v1";

export type Settings = {
  apiKey: string;
  baseUrl: string;
  modelName: string;
};

export const DEFAULT_SETTINGS: Settings = defaults;
```

- [ ] **Step 5: 运行新增的单条测试，确认通过**

Run: `npx vitest run tests/workflow/settings.test.ts -t "default settings is loaded from JSON"`

Expected: PASS。

- [ ] **Step 6: 运行整个测试文件 + tsc + lint**

并行三条命令，任何一条不通过都要停下来排查：

```bash
npx vitest run tests/workflow/settings.test.ts
npx tsc --noEmit
npm run lint
```

Expected: 三条全 PASS。

> **如果 tsc 报错 `Type '{ readonly apiKey: ... }' is not assignable to type 'Settings'`**：
> 把 Step 4 中的赋值改成：`export const DEFAULT_SETTINGS: Settings = defaults as Settings;`

- [ ] **Step 7: 运行完整测试套件，防止其他测试被波及**

Run: `npm test`

Expected: 全部 PASS（前置 4 条 + 新增 1 条 = 至少 5 条 settings 用例通过；其他模块用例也应保持 PASS）。

- [ ] **Step 8: 提交**

```bash
git add src/config/llm-defaults.json src/lib/settings.ts tests/workflow/settings.test.ts
git commit -m "feat(settings): 默认 LLM 配置外置到 JSON,新用户开箱即用"
```

---

## Task 2: 文档更新

**Files:**
- Modify: `CHANGELOG.md`（在 `[Unreleased]` 的 `Changed` 区追加一行）
- Modify: `README.md:37-46`（使用流程第 2 步）
- Modify: `README.md:91-96`（安全提示，追加一条）

- [ ] **Step 1: 更新 CHANGELOG.md**

打开 `CHANGELOG.md`，定位到第 5 行 `### Changed` 之下、第 6 行 `- **重构**: ...` 之上，插入一行（保持已有顺序，新条目放最上面）：

```markdown
- **配置**: 默认 LLM 连接信息（含 API Key）外置到 `src/config/llm-defaults.json`,新用户首次访问无需任何配置即可使用；老用户 localStorage 中的自定义配置仍然优先
```

最终 `### Changed` 第一条应为这一行。

- [ ] **Step 2: 更新 README.md 使用流程**

打开 `README.md`，找到「使用流程」段落（约第 37-46 行）。把第 41-42 行：

```markdown
1. 打开页面，右上角点「设置」
2. 填入你的 LLM API Key、BaseURL、模型名（默认已预填百灵配置）
```

替换为：

```markdown
1. 打开页面，**默认已连通百灵 `Ling-2.6-1T`,可直接跳到第 5 步开始评分**
2. （可选）若需替换 provider,右上角点「设置」,修改 API Key / BaseURL / 模型名
```

- [ ] **Step 3: 更新 README.md 安全提示**

打开 `README.md`，找到「安全提示」段落（约第 91-96 行）。在该段落最后一条（`✅ 建议在 LLM provider 端设置月度额度上限`）之后追加：

```markdown
- ⚠️ 当前仓库已预填演示用的百灵 API Key 到 `src/config/llm-defaults.json`,会随 GH Pages bundle 公开；若你 fork 本项目用于生产,请务必先把 JSON 替换为自己的私有 Key,并在 provider 后台设置月度额度上限
```

- [ ] **Step 4: 重新跑 lint 确认文档改动没破坏什么**

Run: `npm run lint`

Expected: PASS（lint 不检查 md 但确认没误伤）。

- [ ] **Step 5: 提交**

```bash
git add CHANGELOG.md README.md
git commit -m "docs: 同步默认 LLM 配置外置的使用流程与安全提示"
```

---

## Task 3: 端到端手工验证

**Files:** 无代码改动，仅人工核验。

- [ ] **Step 1: 启动开发服务器**

Run: `npm run dev`

Expected: 输出 `Local: http://localhost:5173/` 之类的地址。

- [ ] **Step 2: 浏览器清空 localStorage**

在浏览器打开 `http://localhost:5173/`，按 F12 打开 DevTools → Application → Storage → Local storage → 选中 `http://localhost:5173` → 右键 Clear，或在 Console 跑：

```javascript
localStorage.clear()
```

- [ ] **Step 3: 访问设置页，确认三字段全部预填**

刷新页面 → 点右上角「设置」→ 检查：

- API Key 输入框（密码态）显示有内容（点「显示」可见 `sk-studio-2722acfd3da941e4b2f1326802c5d7d3`）
- Base URL 显示 `https://api.tbox.cn/api/llm/v1/`
- 模型名显示 `Ling-2.6-1T`

Expected: 三字段全部已填好,无空。

- [ ] **Step 4: 点「测试连接」**

点设置页的「测试连接」按钮。

Expected: 几秒后显示 `✓ 连接成功`。

> 若失败，先检查 provider 端 Key 是否仍有效；这不属于本次改动的回归（说明 Key 本身已过期或 provider 改了协议）。

- [ ] **Step 5: 返回主页,确认可直接评分**

点「保存」回主页 → 从下拉选一个内置题目 → 点「开始评分」。

Expected: 评分卡片陆续渲染出来,无 401 / 403 / Network 错误。

- [ ] **Step 6: 停止 dev 服务器**

按 Ctrl+C 终止 `npm run dev`。

---

## Self-Review 结果

**Spec coverage 检查**：

- ✅ 新增 `src/config/llm-defaults.json` → Task 1 Step 3
- ✅ 修改 `src/lib/settings.ts` → Task 1 Step 4
- ✅ tsconfig 不改 → 计划中未触及（已确认 `resolveJsonModule: true`）
- ✅ 行为表的四种场景 → 现有 `loadSettings()` 合并逻辑未动,自动满足
- ✅ 现有测试自动覆盖 → Task 1 Step 7（跑完整套件）
- ✅ 新增测试 → Task 1 Step 1
- ✅ CHANGELOG 更新 → Task 2 Step 1
- ✅ README 使用流程更新 → Task 2 Step 2
- ✅ README 安全提示更新 → Task 2 Step 3
- ✅ 端到端验证清单 → Task 3

**Placeholder 扫描**：无 TBD / TODO / "适当的错误处理" 等占位。所有代码块均完整。

**类型一致性**：`DEFAULT_SETTINGS` / `Settings` / `apiKey` / `baseUrl` / `modelName` 在所有 task 中拼写一致。
