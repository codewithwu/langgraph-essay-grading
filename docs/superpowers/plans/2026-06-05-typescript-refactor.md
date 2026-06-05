# TypeScript 重构与 GitHub Pages 部署实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将现有 Python LangGraph 高考作文评分系统重写为 TypeScript + React + Vite 单页应用，部署到 GitHub Pages。

**Architecture:** 纯前端 SPA。用户在前端自带 LLM API Key（存 localStorage），浏览器内通过 `@langchain/langgraph` 编排 4 节点评分图，直接 fetch LLM Provider 的 OpenAI 兼容 API。

**Tech Stack:** TypeScript 5 (strict) · Vite 5 · React 18 · React Router 6 · @langchain/langgraph · @langchain/openai · Zod · Vitest · ESLint · Prettier · GitHub Actions

**Spec:** `docs/superpowers/specs/2026-06-05-typescript-refactor-design.md`

---

## 文件结构总览

**新增：**
```
package.json                          # npm 包定义
tsconfig.json                         # TS 严格模式
tsconfig.node.json                    # Vite 配置专用
vite.config.ts                        # base: './'
vitest.config.ts                      # 测试配置
index.html                            # Vite HTML 入口
.eslintrc.cjs                         # ESLint 规则
.prettierrc                           # Prettier 配置
.github/workflows/deploy.yml          # GH Actions
src/main.tsx                          # React 入口
src/App.tsx                           # 路由
src/types.ts                          # 共享类型
src/styles/index.css                  # 原 CSS 平移
src/pages/GradingPage.tsx             # 评分主页
src/pages/SettingsPage.tsx            # 设置页
src/workflow/config.ts                # 权重、阈值常量
src/workflow/state.ts                 # Zod + Annotation
src/workflow/prompts.ts               # 提示词
src/workflow/llm.ts                   # ChatOpenAI 工厂
src/workflow/nodes.ts                 # 4 个评分节点
src/workflow/routes.ts                # 路由函数
src/workflow/graph.ts                 # StateGraph
src/components/ScoreCard.tsx
src/components/SkeletonCard.tsx
src/components/FinalScoreCard.tsx
src/components/Header.tsx
src/components/FormSection.tsx
src/components/LoadingBar.tsx
src/hooks/useGradingStream.ts
src/lib/settings.ts
tests/workflow/state.test.ts
tests/workflow/routes.test.ts
tests/workflow/prompts.test.ts
tests/workflow/settings.test.ts
tests/workflow/graph.test.ts
tests/hooks/useGradingStream.test.ts
```

**修改：**
- `.gitignore`（追加 node_modules / dist / coverage）
- `README.md`（改写）
- `CLAUDE.md`（改写为 TS 规范）
- `CHANGELOG.md`（追加 [Unreleased] 条目）

**删除：**
- `langgraph_essay_grading/`（含 `docs/essay_grading_system_langgraph.ipynb`）
- `langchain_agent/`
- `src/main.py` `src/routers/` `src/services/` `src/models/` `src/utils/` `src/static/`
- `main.py` `pyproject.toml` `uv.lock` `.env` `.env.example` `pyproject-editable-install.md` `.python-version` `.venv/`

---

## Task 1: 清理 Python 旧代码

**Files:**
- Delete: 上述「删除」列表中所有路径

- [ ] **Step 1: 删除 Python 目录与文件**

```bash
cd /home/cooper/githubProjects/langgraph-essay-grading
rm -rf langgraph_essay_grading langchain_agent src
rm -f  main.py pyproject.toml uv.lock .env .env.example pyproject-editable-install.md .python-version
rm -rf .venv
```

- [ ] **Step 2: 确认仓库状态**

```bash
git status --short
```

预期：除 `docs/`、`README.md`、`CHANGELOG.md`、`CLAUDE.md`、`LICENSE`、`.gitignore` 外无其他文件。

- [ ] **Step 3: 提交清理**

```bash
git add -A
git commit -m "chore: 删除 Python 旧代码，准备 TypeScript 重构"
```

---

## Task 2: 初始化 npm 项目与 TypeScript 配置

**Files:**
- Create: `package.json`
- Create: `tsconfig.json`
- Create: `tsconfig.node.json`
- Create: `vite.config.ts`
- Create: `vitest.config.ts`
- Create: `index.html`

- [ ] **Step 1: 写入 package.json**

```json
{
  "name": "gaokao-essay-grading",
  "private": true,
  "version": "0.2.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc --noEmit && vite build",
    "preview": "vite preview",
    "test": "vitest run",
    "test:watch": "vitest",
    "lint": "eslint src tests --ext .ts,.tsx",
    "format": "prettier --write \"src/**/*.{ts,tsx,css}\" \"tests/**/*.ts\""
  },
  "dependencies": {
    "@langchain/core": "^0.3.0",
    "@langchain/langgraph": "^0.2.0",
    "@langchain/openai": "^0.3.0",
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "react-router-dom": "^6.26.0",
    "zod": "^3.23.0",
    "zod-to-json-schema": "^3.23.0"
  },
  "devDependencies": {
    "@testing-library/react": "^16.0.0",
    "@types/react": "^18.3.0",
    "@types/react-dom": "^18.3.0",
    "@typescript-eslint/eslint-plugin": "^7.18.0",
    "@typescript-eslint/parser": "^7.18.0",
    "@vitejs/plugin-react": "^4.3.0",
    "eslint": "^8.57.0",
    "eslint-plugin-react": "^7.35.0",
    "eslint-plugin-react-hooks": "^4.6.0",
    "jsdom": "^25.0.0",
    "prettier": "^3.3.0",
    "typescript": "^5.5.0",
    "vite": "^5.4.0",
    "vitest": "^2.0.0"
  }
}
```

- [ ] **Step 2: 写入 tsconfig.json**

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "useDefineForClassFields": true,
    "lib": ["ES2022", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": false,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "esModuleInterop": true,
    "forceConsistentCasingInFileNames": true,
    "types": ["vitest/globals", "node"]
  },
  "include": ["src", "tests"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

- [ ] **Step 3: 写入 tsconfig.node.json**

```json
{
  "compilerOptions": {
    "composite": true,
    "skipLibCheck": true,
    "module": "ESNext",
    "moduleResolution": "bundler",
    "allowSyntheticDefaultImports": true,
    "strict": true
  },
  "include": ["vite.config.ts", "vitest.config.ts"]
}
```

- [ ] **Step 4: 写入 vite.config.ts**

```ts
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  base: "./",
  plugins: [react()],
  build: {
    outDir: "dist",
    sourcemap: false,
  },
});
```

- [ ] **Step 5: 写入 vitest.config.ts**

```ts
import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: "jsdom",
    include: ["tests/**/*.test.ts", "tests/**/*.test.tsx"],
  },
});
```

- [ ] **Step 6: 写入 index.html**

```html
<!DOCTYPE html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>高考作文评分系统</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

- [ ] **Step 7: 提交**

```bash
git add package.json tsconfig.json tsconfig.node.json vite.config.ts vitest.config.ts index.html
git commit -m "chore: 初始化 Vite + React + TypeScript 项目配置"
```

---

## Task 3: 安装依赖

**Files:**
- Create: `package-lock.json`（自动生成）
- Create: `node_modules/`（自动生成，不提交）

- [ ] **Step 1: 配置 npm 镜像（国内网络环境）**

```bash
npm config set registry https://registry.npmmirror.com
```

- [ ] **Step 2: 安装依赖**

```bash
cd /home/cooper/githubProjects/langgraph-essay-grading
npm install
```

预期：安装完成，无致命错误。如个别包下载失败可重试。

- [ ] **Step 3: 验证 dev server 启动**

```bash
timeout 8 npm run dev &
sleep 5
curl -sf http://localhost:5173/ | head -c 200
```

预期：返回 HTML 字符串含 `<div id="root"></div>`。然后 `kill %1`。

- [ ] **Step 4: 提交 lockfile**

```bash
git add package-lock.json
git commit -m "chore: 锁定依赖版本"
```

---

## Task 4: 更新 .gitignore

**Files:**
- Modify: `.gitignore`

- [ ] **Step 1: 在文件末尾追加 Node 相关条目**

```bash
cat >> /home/cooper/githubProjects/langgraph-essay-grading/.gitignore << 'EOF'

# Node / Vite
node_modules/
dist/
coverage/
*.log
.DS_Store
.vite/
EOF
```

- [ ] **Step 2: 验证文件未追踪 node_modules**

```bash
cd /home/cooper/githubProjects/langgraph-essay-grading
git status --ignored --short | head -20
```

预期：`node_modules/` 出现在 ignored 列表中，`dist/` 同样。

- [ ] **Step 3: 提交**

```bash
git add .gitignore
git commit -m "chore: 忽略 node_modules、dist、coverage"
```

---

## Task 5: ESLint + Prettier 配置

**Files:**
- Create: `.eslintrc.cjs`
- Create: `.prettierrc`

- [ ] **Step 1: 写入 .eslintrc.cjs**

```js
module.exports = {
  root: true,
  env: { browser: true, es2022: true, node: true },
  extends: [
    "eslint:recommended",
    "plugin:@typescript-eslint/recommended",
    "plugin:react/recommended",
    "plugin:react-hooks/recommended",
  ],
  parser: "@typescript-eslint/parser",
  parserOptions: { ecmaVersion: 2022, sourceType: "module" },
  settings: { react: { version: "18.3" } },
  rules: {
    "react/react-in-jsx-scope": "off",
    "react/prop-types": "off",
    "@typescript-eslint/no-unused-vars": ["error", { argsIgnorePattern: "^_" }],
  },
  ignorePatterns: ["dist", "node_modules", "*.cjs", "vite.config.ts", "vitest.config.ts"],
};
```

- [ ] **Step 2: 写入 .prettierrc**

```json
{
  "semi": true,
  "singleQuote": false,
  "trailingComma": "all",
  "printWidth": 100,
  "tabWidth": 2
}
```

- [ ] **Step 3: 验证 lint 配置可加载**

```bash
cd /home/cooper/githubProjects/langgraph-essay-grading
npx eslint --print-config src/main.tsx > /dev/null 2>&1 && echo OK
```

（注意：此时 src/main.tsx 还不存在，会报错。等 Task 18 创建 main.tsx 后再验证。先仅做配置文件提交。）

- [ ] **Step 4: 提交**

```bash
git add .eslintrc.cjs .prettierrc
git commit -m "chore: 配置 ESLint 与 Prettier"
```

---

## Task 6: 实现 settings 模块（TDD）

**Files:**
- Create: `src/lib/settings.ts`
- Create: `tests/workflow/settings.test.ts`

- [ ] **Step 1: 写测试**

`tests/workflow/settings.test.ts`：

```ts
import { describe, it, expect, beforeEach } from "vitest";
import { loadSettings, saveSettings, DEFAULT_SETTINGS, type Settings } from "../../src/lib/settings";

describe("settings", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it("returns defaults when storage is empty", () => {
    const s = loadSettings();
    expect(s).toEqual(DEFAULT_SETTINGS);
  });

  it("returns defaults when storage is corrupt JSON", () => {
    localStorage.setItem("grading-settings-v1", "{not valid");
    const s = loadSettings();
    expect(s).toEqual(DEFAULT_SETTINGS);
  });

  it("merges stored values with defaults", () => {
    const partial: Partial<Settings> = { apiKey: "sk-test" };
    localStorage.setItem("grading-settings-v1", JSON.stringify(partial));
    const s = loadSettings();
    expect(s.apiKey).toBe("sk-test");
    expect(s.baseUrl).toBe(DEFAULT_SETTINGS.baseUrl);
  });

  it("round-trips through saveSettings and loadSettings", () => {
    const s: Settings = { apiKey: "k", baseUrl: "https://x", modelName: "m" };
    saveSettings(s);
    expect(loadSettings()).toEqual(s);
  });
});
```

- [ ] **Step 2: 运行测试，确认失败**

```bash
cd /home/cooper/githubProjects/langgraph-essay-grading
npm test -- tests/workflow/settings.test.ts
```

预期：FAIL，提示 `settings` 模块不存在。

- [ ] **Step 3: 实现 src/lib/settings.ts**

```ts
const STORAGE_KEY = "grading-settings-v1";

export type Settings = {
  apiKey: string;
  baseUrl: string;
  modelName: string;
};

export const DEFAULT_SETTINGS: Settings = {
  apiKey: "",
  baseUrl: "https://api.bailing.cn/v1",
  modelName: "Ling-2.6-flash",
};

export function loadSettings(): Settings {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return DEFAULT_SETTINGS;
    return { ...DEFAULT_SETTINGS, ...JSON.parse(raw) };
  } catch {
    return DEFAULT_SETTINGS;
  }
}

export function saveSettings(s: Settings): void {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(s));
}
```

- [ ] **Step 4: 重新运行测试，确认通过**

```bash
npm test -- tests/workflow/settings.test.ts
```

预期：4 个用例全部 PASS。

- [ ] **Step 5: 提交**

```bash
git add src/lib/settings.ts tests/workflow/settings.test.ts
git commit -m "feat(settings): 实现 localStorage 读写与默认配置"
```

---

## Task 7: 实现 state 模块（TDD：Zod schema 验证）

**Files:**
- Create: `src/workflow/state.ts`
- Create: `tests/workflow/state.test.ts`

- [ ] **Step 1: 写测试**

`tests/workflow/state.test.ts`：

```ts
import { describe, it, expect } from "vitest";
import { ScoreDetail } from "../../src/workflow/state";

describe("ScoreDetail schema", () => {
  it("accepts valid input", () => {
    const r = ScoreDetail.safeParse({ score: 0.8, reason: "good" });
    expect(r.success).toBe(true);
  });

  it("rejects score < 0", () => {
    const r = ScoreDetail.safeParse({ score: -0.1, reason: "" });
    expect(r.success).toBe(false);
  });

  it("rejects score > 1", () => {
    const r = ScoreDetail.safeParse({ score: 1.1, reason: "" });
    expect(r.success).toBe(false);
  });

  it("rejects missing fields", () => {
    const r = ScoreDetail.safeParse({});
    expect(r.success).toBe(false);
  });
});
```

- [ ] **Step 2: 运行测试，确认失败**

```bash
cd /home/cooper/githubProjects/langgraph-essay-grading
npm test -- tests/workflow/state.test.ts
```

预期：FAIL，`state` 模块不存在。

- [ ] **Step 3: 实现 src/workflow/state.ts**

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
  final_score: Annotation<number>(),
});

export type EssayStateType = typeof EssayState.State;
```

- [ ] **Step 4: 重新运行测试，确认通过**

```bash
npm test -- tests/workflow/state.test.ts
```

预期：4 个用例全部 PASS。

- [ ] **Step 5: 提交**

```bash
git add src/workflow/state.ts tests/workflow/state.test.ts
git commit -m "feat(state): 定义 Zod ScoreDetail 与 LangGraph EssayState"
```

---

## Task 8: 实现 prompts 模块（TDD）

**Files:**
- Create: `src/workflow/prompts.ts`
- Create: `tests/workflow/prompts.test.ts`

- [ ] **Step 1: 写测试**

`tests/workflow/prompts.test.ts`：

```ts
import { describe, it, expect } from "vitest";
import { z } from "zod";
import { SYSTEM_PROMPT, buildPrompt } from "../../src/workflow/prompts";

const TestSchema = z.object({
  score: z.number(),
  label: z.string(),
});

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

describe("SYSTEM_PROMPT", () => {
  it("mentions 高考", () => {
    expect(SYSTEM_PROMPT).toContain("高考");
  });

  it("specifies score range 0~1", () => {
    expect(SYSTEM_PROMPT).toMatch(/0[~～-]1|0\s*到\s*1/);
  });
});
```

- [ ] **Step 2: 运行测试，确认失败**

```bash
cd /home/cooper/githubProjects/langgraph-essay-grading
npm test -- tests/workflow/prompts.test.ts
```

预期：FAIL，`prompts` 模块不存在。

- [ ] **Step 3: 实现 src/workflow/prompts.ts**

```ts
import type { z } from "zod";
import { zodToJsonSchema } from "zod-to-json-schema";

export const SYSTEM_PROMPT = `你是一名经验丰富的高考作文阅卷老师。请遵循以下准则：
1. 严格按照高考作文评分标准进行评判
2. 客观公正，不受作文主题立场影响
3. 评分理由要具体、有依据，引用作文原文
4. 每个维度独立评分，不因某维度表现好而影响其他维度
5. 评分范围 0~1，0.6 为及格线，0.8 以上为优秀`;

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

- [ ] **Step 4: 重新运行测试，确认通过**

```bash
npm test -- tests/workflow/prompts.test.ts
```

预期：6 个用例全部 PASS。

- [ ] **Step 5: 提交**

```bash
git add src/workflow/prompts.ts tests/workflow/prompts.test.ts
git commit -m "feat(prompts): 系统提示词与 JSON schema 提示构建"
```

---

## Task 9: 实现 config 常量

**Files:**
- Create: `src/workflow/config.ts`

- [ ] **Step 1: 写入 src/workflow/config.ts**

```ts
export const WEIGHT_RELEVANCE = 0.3;
export const WEIGHT_EVIDENCE = 0.2;
export const WEIGHT_STRUCTURE = 0.2;
export const WEIGHT_EXPRESSION = 0.3;

export const RELEVANCE_THRESHOLD = 0.5;

export const NODE_NAMES = {
  RELEVANCE: "check_relevance",
  EVIDENCE: "check_evidence",
  STRUCTURE: "check_structure",
  EXPRESSION: "check_expression",
  FAN_OUT: "fan_out",
  CALCULATE: "calculate_final_score",
} as const;
```

- [ ] **Step 2: 验证 TS 编译**

```bash
cd /home/cooper/githubProjects/langgraph-essay-grading
npx tsc --noEmit
```

预期：无错误。

- [ ] **Step 3: 提交**

```bash
git add src/workflow/config.ts
git commit -m "feat(config): 评分权重、阈值与节点名常量"
```

---

## Task 10: 实现 routes 模块（TDD）

**Files:**
- Create: `src/workflow/routes.ts`
- Create: `tests/workflow/routes.test.ts`

- [ ] **Step 1: 写测试**

`tests/workflow/routes.test.ts`：

```ts
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
```

- [ ] **Step 2: 运行测试，确认失败**

```bash
cd /home/cooper/githubProjects/langgraph-essay-grading
npm test -- tests/workflow/routes.test.ts
```

预期：FAIL，`routes` 模块不存在。

- [ ] **Step 3: 实现 src/workflow/routes.ts**

```ts
import { RELEVANCE_THRESHOLD } from "./config";
import type { EssayStateType } from "./state";

export function routeRelevance(
  state: EssayStateType,
): "fan_out" | "calculate_final_score" {
  return state.relevance.score > RELEVANCE_THRESHOLD
    ? "fan_out"
    : "calculate_final_score";
}
```

- [ ] **Step 4: 重新运行测试，确认通过**

```bash
npm test -- tests/workflow/routes.test.ts
```

预期：5 个用例全部 PASS。

- [ ] **Step 5: 提交**

```bash
git add src/workflow/routes.ts tests/workflow/routes.test.ts
git commit -m "feat(routes): 审题条件路由（>0.5 才并行评分）"
```

---

## Task 11: 实现 LLM 工厂

**Files:**
- Create: `src/workflow/llm.ts`

- [ ] **Step 1: 写入 src/workflow/llm.ts**

```ts
import { ChatOpenAI } from "@langchain/openai";
import { loadSettings } from "../lib/settings";

export function getLLM(): ChatOpenAI {
  const { apiKey, baseUrl, modelName } = loadSettings();
  return new ChatOpenAI({
    apiKey,
    configuration: { baseURL: baseUrl },
    model: modelName,
    temperature: 0,
    maxTokens: 2000,
    timeout: 60_000,
  });
}
```

- [ ] **Step 2: 验证 TS 编译**

```bash
cd /home/cooper/githubProjects/langgraph-essay-grading
npx tsc --noEmit
```

预期：无错误。

- [ ] **Step 3: 提交**

```bash
git add src/workflow/llm.ts
git commit -m "feat(llm): 从 localStorage 配置创建 ChatOpenAI 实例"
```

---

## Task 12: 实现 4 个评分节点

**Files:**
- Create: `src/workflow/nodes.ts`

- [ ] **Step 1: 写入 src/workflow/nodes.ts**

```ts
import { HumanMessage, SystemMessage } from "@langchain/core/messages";
import { ScoreDetail, type EssayStateType } from "./state";
import { SYSTEM_PROMPT, buildPrompt } from "./prompts";
import { getLLM } from "./llm";
import {
  WEIGHT_EVIDENCE,
  WEIGHT_EXPRESSION,
  WEIGHT_RELEVANCE,
  WEIGHT_STRUCTURE,
} from "./config";

type Dim = "relevance" | "evidence" | "structure" | "expression";

const DIM_INSTRUCTIONS: Record<Dim, string> = {
  relevance: "请评估以下高考作文的审题立意。考察是否切题、立意是否深刻。",
  evidence: "请评估以下高考作文的论据分析。考察材料是否充实、论据是否有力。",
  structure: "请评估以下高考作文的结构。考察行文逻辑、段落衔接是否合理。",
  expression: "请评估以下高考作文的语言文采。考察用词是否贴切、修辞是否恰当、句式是否灵活。",
};

async function gradeDim(
  state: EssayStateType,
  dim: Dim,
): Promise<Partial<EssayStateType>> {
  const llm = getLLM().withStructuredOutput(ScoreDetail);
  const messages = [
    new SystemMessage(buildPrompt(ScoreDetail) + SYSTEM_PROMPT),
    new HumanMessage(
      `${DIM_INSTRUCTIONS[dim]}\n给出 0 到 1 之间的分数，并说明理由。\n\n题目：${state.topic}\n\n作文：${state.essay}`,
    ),
  ];
  return { [dim]: await llm.invoke(messages) } as Partial<EssayStateType>;
}

export async function check_relevance(
  state: EssayStateType,
): Promise<Partial<EssayStateType>> {
  return gradeDim(state, "relevance");
}

export async function check_evidence(
  state: EssayStateType,
): Promise<Partial<EssayStateType>> {
  return gradeDim(state, "evidence");
}

export async function check_structure(
  state: EssayStateType,
): Promise<Partial<EssayStateType>> {
  return gradeDim(state, "structure");
}

export async function check_expression(
  state: EssayStateType,
): Promise<Partial<EssayStateType>> {
  return gradeDim(state, "expression");
}

export function calculate_final_score(
  state: EssayStateType,
): Partial<EssayStateType> {
  const final =
    state.relevance.score * WEIGHT_RELEVANCE +
    state.evidence.score * WEIGHT_EVIDENCE +
    state.structure.score * WEIGHT_STRUCTURE +
    state.expression.score * WEIGHT_EXPRESSION;
  return { final_score: Math.round(final * 100) / 100 };
}
```

- [ ] **Step 2: 验证 TS 编译**

```bash
cd /home/cooper/githubProjects/langgraph-essay-grading
npx tsc --noEmit
```

预期：无错误。

- [ ] **Step 3: 提交**

```bash
git add src/workflow/nodes.ts
git commit -m "feat(nodes): 4 维度评分节点与加权总分计算"
```

---

## Task 13: 构建 StateGraph（TDD：mocked LLM）

**Files:**
- Create: `src/workflow/graph.ts`
- Create: `tests/workflow/graph.test.ts`

- [ ] **Step 1: 写测试**

`tests/workflow/graph.test.ts`：

```ts
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
```

- [ ] **Step 2: 运行测试，确认失败**

```bash
cd /home/cooper/githubProjects/langgraph-essay-grading
npm test -- tests/workflow/graph.test.ts
```

预期：FAIL，`graph` 模块不存在。

- [ ] **Step 3: 实现 src/workflow/graph.ts**

```ts
import { END, START, StateGraph } from "@langchain/langgraph";
import { EssayState, type EssayStateType } from "./state";
import {
  calculate_final_score,
  check_evidence,
  check_expression,
  check_relevance,
  check_structure,
} from "./nodes";
import { routeRelevance } from "./routes";
import { NODE_NAMES } from "./config";

function fanOut(_: EssayStateType): Record<string, never> {
  return {};
}

const workflow = new StateGraph(EssayState)
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
  .addEdge(NODE_NAMES.CALCULATE, END);

export const graph = workflow.compile();
```

- [ ] **Step 4: 重新运行测试，确认通过**

```bash
npm test -- tests/workflow/graph.test.ts
```

预期：2 个用例全部 PASS。

- [ ] **Step 5: 提交**

```bash
git add src/workflow/graph.ts tests/workflow/graph.test.ts
git commit -m "feat(graph): 构建审题→并行→总分的 StateGraph"
```

---

## Task 14: 实现 useGradingStream Hook（TDD）

**Files:**
- Create: `src/hooks/useGradingStream.ts`
- Create: `tests/hooks/useGradingStream.test.ts`

- [ ] **Step 1: 写测试**

`tests/hooks/useGradingStream.test.ts`：

```ts
import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, act } from "@testing-library/react";

vi.mock("../../src/workflow/graph", () => {
  return {
    graph: {
      stream: async function* () {
        yield { check_relevance: { relevance: { score: 0.9, reason: "good" } } };
        yield { check_evidence: { evidence: { score: 0.7, reason: "ok" } } };
        yield {
          calculate_final_score: { final_score: 0.8 },
        };
      },
    },
  };
});

import { useGradingStream } from "../../src/hooks/useGradingStream";

describe("useGradingStream", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("starts with empty events, not running, not done", () => {
    const { result } = renderHook(() => useGradingStream());
    expect(result.current.events).toEqual([]);
    expect(result.current.running).toBe(false);
    expect(result.current.done).toBe(false);
  });

  it("run() collects events and sets done=true", async () => {
    const { result } = renderHook(() => useGradingStream());

    await act(async () => {
      await result.current.run({ topic: "t", essay: "e" });
    });

    expect(result.current.events.length).toBe(3);
    expect(result.current.events[0].node).toBe("check_relevance");
    expect(result.current.done).toBe(true);
    expect(result.current.running).toBe(false);
  });

  it("resets state between runs", async () => {
    const { result } = renderHook(() => useGradingStream());

    await act(async () => {
      await result.current.run({ topic: "t", essay: "e" });
    });
    expect(result.current.events.length).toBe(3);

    await act(async () => {
      await result.current.run({ topic: "t2", essay: "e2" });
    });
    expect(result.current.events.length).toBe(3);
  });
});
```

- [ ] **Step 2: 运行测试，确认失败**

```bash
cd /home/cooper/githubProjects/langgraph-essay-grading
npm test -- tests/hooks/useGradingStream.test.ts
```

预期：FAIL，`useGradingStream` 模块不存在。

- [ ] **Step 3: 实现 src/hooks/useGradingStream.ts**

```ts
import { useCallback, useState } from "react";
import { graph } from "../workflow/graph";
import type { EssayStateType } from "../workflow/state";

export type StreamEvent = {
  node: string;
  update: Record<string, unknown>;
};

export function useGradingStream() {
  const [events, setEvents] = useState<StreamEvent[]>([]);
  const [done, setDone] = useState(false);
  const [running, setRunning] = useState(false);

  const run = useCallback(async (state: Pick<EssayStateType, "topic" | "essay">) => {
    setEvents([]);
    setDone(false);
    setRunning(true);
    try {
      const stream = await graph.stream(state, { streamMode: "updates" });
      for await (const event of stream) {
        for (const [node, update] of Object.entries(event)) {
          setEvents((prev) => [...prev, { node, update: update as Record<string, unknown> }]);
        }
      }
    } finally {
      setDone(true);
      setRunning(false);
    }
  }, []);

  return { events, done, running, run };
}
```

- [ ] **Step 4: 重新运行测试，确认通过**

```bash
npm test -- tests/hooks/useGradingStream.test.ts
```

预期：3 个用例全部 PASS。

- [ ] **Step 5: 提交**

```bash
git add src/hooks/useGradingStream.ts tests/hooks/useGradingStream.test.ts
git commit -m "feat(hook): useGradingStream 订阅 graph 流事件"
```

---

## Task 15: 迁移原 CSS 到独立文件

**Files:**
- Create: `src/styles/index.css`

- [ ] **Step 1: 写入 src/styles/index.css**

（平移原 `src/static/index.html` 中的 `<style>` 块全部内容。）

```css
* { margin: 0; padding: 0; box-sizing: border-box; }

body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
  background: #f5f7fa;
  color: #2c3e50;
  line-height: 1.6;
  min-height: 100vh;
}

.container {
  max-width: 960px;
  margin: 0 auto;
  padding: 40px 20px;
}

h1 {
  text-align: center;
  font-size: 28px;
  font-weight: 700;
  color: #1a1a2e;
  margin-bottom: 8px;
}

.subtitle {
  text-align: center;
  color: #7f8c8d;
  font-size: 14px;
  margin-bottom: 40px;
}

.app-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.app-header h1 { margin-bottom: 0; }

.icon-btn {
  background: transparent;
  border: 1.5px solid #dfe6e9;
  border-radius: 8px;
  padding: 6px 10px;
  cursor: pointer;
  font-size: 16px;
  color: #34495e;
  transition: all 0.2s;
}
.icon-btn:hover { border-color: #4a90d9; color: #4a90d9; }

.form-section {
  background: #fff;
  border-radius: 12px;
  padding: 32px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.06);
  margin-bottom: 32px;
}

.form-group { margin-bottom: 20px; }

label {
  display: block;
  font-weight: 600;
  font-size: 14px;
  color: #34495e;
  margin-bottom: 6px;
}

input[type="text"], input[type="password"], input[type="url"], textarea {
  width: 100%;
  padding: 12px 16px;
  border: 1.5px solid #dfe6e9;
  border-radius: 8px;
  font-size: 15px;
  font-family: inherit;
  transition: border-color 0.2s, box-shadow 0.2s;
  background: #fafbfc;
}

input:focus, textarea:focus {
  outline: none;
  border-color: #4a90d9;
  box-shadow: 0 0 0 3px rgba(74,144,217,0.12);
  background: #fff;
}

textarea { min-height: 200px; resize: vertical; }

.btn-submit {
  display: block;
  width: 100%;
  padding: 14px;
  background: linear-gradient(135deg, #4a90d9, #357abd);
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
}
.btn-submit:hover:not(:disabled) {
  background: linear-gradient(135deg, #357abd, #2a6496);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(74,90,217,0.3);
}
.btn-submit:disabled { opacity: 0.7; cursor: not-allowed; }

.btn-row { display: flex; gap: 12px; }
.btn-row .btn-submit { flex: 1; }

.loading-bar { display: none; margin-top: 16px; text-align: center; }
.loading-bar.active { display: block; }

.loading-dots { display: inline-flex; gap: 6px; margin-bottom: 8px; }
.loading-dots span {
  width: 8px; height: 8px;
  background: #4a90d9;
  border-radius: 50%;
  animation: pulse 1.4s ease-in-out infinite;
}
.loading-dots span:nth-child(2) { animation-delay: 0.2s; }
.loading-dots span:nth-child(3) { animation-delay: 0.4s; }

@keyframes pulse {
  0%, 80%, 100% { transform: scale(0.6); opacity: 0.4; }
  40% { transform: scale(1); opacity: 1; }
}

.loading-text { font-size: 14px; color: #7f8c8d; }

.results-section { display: none; }
.results-section.active { display: block; }

.section-title {
  font-size: 18px;
  font-weight: 600;
  color: #1a1a2e;
  margin-bottom: 16px;
  padding-left: 12px;
  border-left: 3px solid #4a90d9;
}

.score-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.score-card {
  background: #fff;
  border-radius: 10px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
  animation: slideIn 0.4s ease-out;
}

@keyframes slideIn {
  from { opacity: 0; transform: translateY(12px); }
  to { opacity: 1; transform: translateY(0); }
}

.score-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.score-card-title { font-size: 15px; font-weight: 600; color: #34495e; }

.score-badge {
  font-size: 20px;
  font-weight: 700;
  padding: 4px 12px;
  border-radius: 20px;
  min-width: 56px;
  text-align: center;
}

.score-high { background: #e8f5e9; color: #2e7d32; }
.score-mid  { background: #fff3e0; color: #e65100; }
.score-low  { background: #ffebee; color: #c62828; }

.score-reason { font-size: 13px; color: #636e72; line-height: 1.7; }

.skeleton-card {
  background: #fff;
  border-radius: 10px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}

.skeleton-line {
  height: 14px;
  background: linear-gradient(90deg, #eee 25%, #f5f5f5 50%, #eee 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
  border-radius: 4px;
  margin-bottom: 10px;
}
.skeleton-line.short { width: 40%; }
.skeleton-line.medium { width: 70%; }
.skeleton-line.long { width: 100%; }

@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

.final-score-card {
  background: linear-gradient(135deg, #1a1a2e, #16213e);
  border-radius: 12px;
  padding: 32px;
  text-align: center;
  color: #fff;
  animation: slideIn 0.5s ease-out;
  display: none;
}
.final-score-card.active { display: block; }

.final-score-label { font-size: 14px; opacity: 0.7; margin-bottom: 8px; }
.final-score-value { font-size: 56px; font-weight: 800; letter-spacing: -2px; }
.final-score-unit { font-size: 16px; opacity: 0.5; margin-left: 4px; }

.toast {
  position: fixed;
  top: 20px;
  left: 50%;
  transform: translateX(-50%);
  background: #c62828;
  color: #fff;
  padding: 12px 20px;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
  z-index: 1000;
  animation: slideIn 0.3s ease-out;
}

.field-help { font-size: 12px; color: #95a5a6; margin-top: 6px; }
.input-with-toggle { display: flex; gap: 8px; }
.input-with-toggle input { flex: 1; }

@media (max-width: 640px) {
  .score-grid { grid-template-columns: 1fr; }
  .container { padding: 20px 16px; }
  h1 { font-size: 22px; }
  .app-header { flex-direction: column; gap: 12px; }
}
```

- [ ] **Step 2: 提交**

```bash
git add src/styles/index.css
git commit -m "feat(styles): 迁移原视觉样式并扩展响应式布局"
```

---

## Task 16: 实现展示类组件

**Files:**
- Create: `src/components/ScoreCard.tsx`
- Create: `src/components/SkeletonCard.tsx`
- Create: `src/components/FinalScoreCard.tsx`

- [ ] **Step 1: 写入 src/components/ScoreCard.tsx**

```tsx
import type { ScoreDetail } from "../workflow/state";

type Props = {
  title: string;
  detail: ScoreDetail;
};

function scoreClass(score: number): string {
  if (score >= 0.8) return "score-high";
  if (score >= 0.6) return "score-mid";
  return "score-low";
}

export function ScoreCard({ title, detail }: Props) {
  return (
    <div className="score-card">
      <div className="score-card-header">
        <span className="score-card-title">{title}</span>
        <span className={`score-badge ${scoreClass(detail.score)}`}>
          {detail.score.toFixed(2)}
        </span>
      </div>
      <p className="score-reason">{detail.reason}</p>
    </div>
  );
}
```

- [ ] **Step 2: 写入 src/components/SkeletonCard.tsx**

```tsx
export function SkeletonCard() {
  return (
    <div className="skeleton-card">
      <div className="skeleton-line short" />
      <div className="skeleton-line long" />
      <div className="skeleton-line medium" />
    </div>
  );
}
```

- [ ] **Step 3: 写入 src/components/FinalScoreCard.tsx**

```tsx
type Props = { score: number; visible: boolean };

export function FinalScoreCard({ score, visible }: Props) {
  return (
    <div className={`final-score-card ${visible ? "active" : ""}`}>
      <div className="final-score-label">综合评分</div>
      <div className="final-score-value">
        <span>{score.toFixed(2)}</span>
        <span className="final-score-unit">/ 1</span>
      </div>
    </div>
  );
}
```

- [ ] **Step 4: 验证 TS 编译**

```bash
cd /home/cooper/githubProjects/langgraph-essay-grading
npx tsc --noEmit
```

预期：无错误。

- [ ] **Step 5: 提交**

```bash
git add src/components/ScoreCard.tsx src/components/SkeletonCard.tsx src/components/FinalScoreCard.tsx
git commit -m "feat(components): ScoreCard、SkeletonCard、FinalScoreCard"
```

---

## Task 17: 实现交互类组件

**Files:**
- Create: `src/components/Header.tsx`
- Create: `src/components/FormSection.tsx`
- Create: `src/components/LoadingBar.tsx`

- [ ] **Step 1: 写入 src/components/Header.tsx**

```tsx
import { Link } from "react-router-dom";

type Props = { title: string; subtitle: string };

export function Header({ title, subtitle }: Props) {
  return (
    <div className="app-header">
      <div>
        <h1>{title}</h1>
        <p className="subtitle">{subtitle}</p>
      </div>
      <Link to="/settings" className="icon-btn" aria-label="设置">⚙ 设置</Link>
    </div>
  );
}
```

- [ ] **Step 2: 写入 src/components/FormSection.tsx**

```tsx
import { useState, type FormEvent } from "react";

type Props = {
  disabled: boolean;
  onSubmit: (topic: string, essay: string) => void;
};

export function FormSection({ disabled, onSubmit }: Props) {
  const [topic, setTopic] = useState("");
  const [essay, setEssay] = useState("");

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

  return (
    <form className="form-section" onSubmit={handleSubmit}>
      <div className="form-group">
        <label htmlFor="topic">作文题目</label>
        <input
          type="text"
          id="topic"
          placeholder="请输入作文题目..."
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

- [ ] **Step 3: 写入 src/components/LoadingBar.tsx**

```tsx
type Props = { visible: boolean; text: string };

export function LoadingBar({ visible, text }: Props) {
  return (
    <div className={`loading-bar ${visible ? "active" : ""}`}>
      <div className="loading-dots">
        <span /><span /><span />
      </div>
      <div className="loading-text">{text}</div>
    </div>
  );
}
```

- [ ] **Step 4: 验证 TS 编译**

```bash
cd /home/cooper/githubProjects/langgraph-essay-grading
npx tsc --noEmit
```

预期：无错误。

- [ ] **Step 5: 提交**

```bash
git add src/components/Header.tsx src/components/FormSection.tsx src/components/LoadingBar.tsx
git commit -m "feat(components): Header、FormSection、LoadingBar"
```

---

## Task 18: 实现 GradingPage

**Files:**
- Create: `src/pages/GradingPage.tsx`

- [ ] **Step 1: 写入 src/pages/GradingPage.tsx**

```tsx
import { useEffect, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { Header } from "../components/Header";
import { FormSection } from "../components/FormSection";
import { LoadingBar } from "../components/LoadingBar";
import { ScoreCard } from "../components/ScoreCard";
import { SkeletonCard } from "../components/SkeletonCard";
import { FinalScoreCard } from "../components/FinalScoreCard";
import { useGradingStream } from "../hooks/useGradingStream";
import { loadSettings } from "../lib/settings";
import type { ScoreDetail } from "../workflow/state";
import { NODE_NAMES } from "../workflow/config";

const NODE_LABELS: Record<string, string> = {
  [NODE_NAMES.RELEVANCE]: "审题立意",
  [NODE_NAMES.EVIDENCE]: "论据分析",
  [NODE_NAMES.STRUCTURE]: "结构评估",
  [NODE_NAMES.EXPRESSION]: "语言文采",
};

const LOADING_TEXTS: Record<string, string> = {
  [NODE_NAMES.RELEVANCE]: "智能体正在审题...",
  [NODE_NAMES.FAN_OUT]: "审题完成，正在启动多维度并行评分...",
  [NODE_NAMES.EVIDENCE]: "正在分析论据...",
  [NODE_NAMES.STRUCTURE]: "正在评估结构...",
  [NODE_NAMES.EXPRESSION]: "正在鉴赏语言...",
  [NODE_NAMES.CALCULATE]: "正在计算综合评分...",
};

const PARALLEL_DIMS = [NODE_NAMES.EVIDENCE, NODE_NAMES.STRUCTURE, NODE_NAMES.EXPRESSION] as const;

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
  const { events, done, running, run } = useGradingStream();

  useEffect(() => {
    if (!loadSettings().apiKey) navigate("/settings", { replace: true });
  }, [navigate]);

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

  function handleSubmit(topic: string, essay: string) {
    run({ topic, essay }).catch((err) => alert(`评分请求失败: ${err.message ?? err}`));
  }

  const showResults = events.length > 0;

  return (
    <div className="container">
      <Header title="高考作文评分系统" subtitle="基于 LangGraph 的多维度智能评分" />

      <FormSection disabled={running} onSubmit={handleSubmit} />
      <LoadingBar visible={running} text={done ? "评分完成" : latestLoadingText} />

      <div className={`results-section ${showResults ? "active" : ""}`}>
        {showResults && <h2 className="section-title">多维度评分</h2>}
        <div className="score-grid">
          {relevanceEvent && (() => {
            const d = extractScoreDetail(NODE_NAMES.RELEVANCE, relevanceEvent.update);
            return d ? <ScoreCard title={NODE_LABELS[NODE_NAMES.RELEVANCE]} detail={d} /> : null;
          })()}

          {PARALLEL_DIMS.map((dim) => {
            const event = events.find((e) => e.node === dim);
            if (event) {
              const d = extractScoreDetail(dim, event.update);
              if (d) return <ScoreCard key={dim} title={NODE_LABELS[dim]} detail={d} />;
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

- [ ] **Step 2: 验证 TS 编译**

```bash
cd /home/cooper/githubProjects/langgraph-essay-grading
npx tsc --noEmit
```

预期：无错误。

- [ ] **Step 3: 提交**

```bash
git add src/pages/GradingPage.tsx
git commit -m "feat(pages): GradingPage 组合所有评分 UI 组件"
```

---

## Task 19: 实现 SettingsPage

**Files:**
- Create: `src/pages/SettingsPage.tsx`

- [ ] **Step 1: 写入 src/pages/SettingsPage.tsx**

```tsx
import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { DEFAULT_SETTINGS, loadSettings, saveSettings, type Settings } from "../lib/settings";
import { getLLM } from "../workflow/llm";
import { Header } from "../components/Header";

export function SettingsPage() {
  const navigate = useNavigate();
  const [apiKey, setApiKey] = useState(loadSettings().apiKey);
  const [baseUrl, setBaseUrl] = useState(loadSettings().baseUrl);
  const [modelName, setModelName] = useState(loadSettings().modelName);
  const [showKey, setShowKey] = useState(false);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<string | null>(null);

  function handleSave(e: FormEvent) {
    e.preventDefault();
    const s: Settings = { apiKey: apiKey.trim(), baseUrl: baseUrl.trim(), modelName: modelName.trim() };
    saveSettings(s);
    navigate("/");
  }

  async function handleTest() {
    setTesting(true);
    setTestResult(null);
    try {
      saveSettings({ apiKey: apiKey.trim(), baseUrl: baseUrl.trim(), modelName: modelName.trim() });
      const llm = getLLM();
      await llm.invoke([{ role: "user", content: "hi" }]);
      setTestResult("✓ 连接成功");
    } catch (err) {
      setTestResult(`✗ 失败: ${err instanceof Error ? err.message : String(err)}`);
    } finally {
      setTesting(false);
    }
  }

  function handleReset() {
    setApiKey(DEFAULT_SETTINGS.apiKey);
    setBaseUrl(DEFAULT_SETTINGS.baseUrl);
    setModelName(DEFAULT_SETTINGS.modelName);
  }

  return (
    <div className="container">
      <Header title="LLM 连接设置" subtitle="配置 API Key、BaseURL 与模型名（存于浏览器 localStorage）" />

      <form className="form-section" onSubmit={handleSave}>
        <div className="form-group">
          <label htmlFor="apiKey">API Key</label>
          <div className="input-with-toggle">
            <input
              type={showKey ? "text" : "password"}
              id="apiKey"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder="sk-..."
              autoComplete="off"
            />
            <button
              type="button"
              className="icon-btn"
              onClick={() => setShowKey((s) => !s)}
            >
              {showKey ? "隐藏" : "显示"}
            </button>
          </div>
          <div className="field-help">请使用额度受限的 Key，避免被盗刷</div>
        </div>

        <div className="form-group">
          <label htmlFor="baseUrl">Base URL</label>
          <input
            type="url"
            id="baseUrl"
            value={baseUrl}
            onChange={(e) => setBaseUrl(e.target.value)}
            placeholder={DEFAULT_SETTINGS.baseUrl}
          />
        </div>

        <div className="form-group">
          <label htmlFor="modelName">模型名</label>
          <input
            type="text"
            id="modelName"
            value={modelName}
            onChange={(e) => setModelName(e.target.value)}
            placeholder={DEFAULT_SETTINGS.modelName}
          />
        </div>

        <div className="btn-row">
          <button type="submit" className="btn-submit">保存</button>
          <button type="button" className="btn-submit" onClick={handleTest} disabled={testing || !apiKey}>
            {testing ? "测试中..." : "测试连接"}
          </button>
        </div>

        <div className="btn-row" style={{ marginTop: 12 }}>
          <button type="button" className="btn-submit" onClick={handleReset}>恢复默认</button>
        </div>

        {testResult && (
          <div className="field-help" style={{ marginTop: 12, fontSize: 14 }}>
            {testResult}
          </div>
        )}
      </form>
    </div>
  );
}
```

- [ ] **Step 2: 验证 TS 编译**

```bash
cd /home/cooper/githubProjects/langgraph-essay-grading
npx tsc --noEmit
```

预期：无错误。

- [ ] **Step 3: 提交**

```bash
git add src/pages/SettingsPage.tsx
git commit -m "feat(pages): SettingsPage 配置 API Key、BaseURL、模型名"
```

---

## Task 20: 实现 App 路由与 main 入口

**Files:**
- Create: `src/App.tsx`
- Create: `src/main.tsx`
- Create: `src/types.ts`（占位，避免空目录问题）

- [ ] **Step 1: 写入 src/App.tsx**

```tsx
import { BrowserRouter, HashRouter, Route, Routes } from "react-router-dom";
import { GradingPage } from "./pages/GradingPage";
import { SettingsPage } from "./pages/SettingsPage";

const Router = import.meta.env.PROD ? HashRouter : BrowserRouter;

export function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<GradingPage />} />
        <Route path="/settings" element={<SettingsPage />} />
        <Route path="*" element={<GradingPage />} />
      </Routes>
    </Router>
  );
}
```

> 注：用 HashRouter 兼容 GH Pages 子路径 + 直接刷新页面，dev 用 BrowserRouter 享受正常 URL。

- [ ] **Step 2: 写入 src/main.tsx**

```tsx
import React from "react";
import ReactDOM from "react-dom/client";
import { App } from "./App";
import "./styles/index.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
```

- [ ] **Step 3: 写入 src/types.ts**

```ts
export {};
```

- [ ] **Step 4: 验证 TS 编译**

```bash
cd /home/cooper/githubProjects/langgraph-essay-grading
npx tsc --noEmit
```

预期：无错误。

- [ ] **Step 5: 启动 dev server 自测**

```bash
timeout 10 npm run dev &
sleep 6
curl -sf http://localhost:5173/ | head -c 300
```

预期：返回 HTML 含 `<div id="root"></div>`。然后 `kill %1`。

- [ ] **Step 6: 提交**

```bash
git add src/App.tsx src/main.tsx src/types.ts
git commit -m "feat(app): React Router 入口与根组件"
```

---

## Task 21: 添加 GitHub Pages 部署工作流

**Files:**
- Create: `.github/workflows/deploy.yml`

- [ ] **Step 1: 写入 .github/workflows/deploy.yml**

```yaml
name: Deploy to GitHub Pages

on:
  push:
    branches: [main]
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: pages
  cancel-in-progress: false

jobs:
  build-deploy:
    runs-on: ubuntu-latest
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: npm
      - run: npm ci
      - run: npm run build
      - uses: actions/configure-pages@v5
      - uses: actions/upload-pages-artifact@v3
        with:
          path: dist
      - id: deployment
        uses: actions/deploy-pages@v4
```

- [ ] **Step 2: 提交**

```bash
git add .github/workflows/deploy.yml
git commit -m "ci: 添加 GitHub Pages 自动部署工作流"
```

---

## Task 22: 更新 CHANGELOG

**Files:**
- Modify: `CHANGELOG.md`

- [ ] **Step 1: 替换 CHANGELOG.md 内容**

```markdown
# Changelog

## [Unreleased]

### Changed
- **重构**: 整个项目从 Python (FastAPI + LangGraph) 迁移到 TypeScript (Vite + React)
- **架构**: 从后端 + 前端架构改为纯前端 SPA，LLM API Key 由用户在浏览器内配置
- **部署目标**: 改为 GitHub Pages 静态部署

### Added
- React + TypeScript 前端，保留原版 UI 视觉
- `/settings` 页面管理 LLM 连接信息（API Key / BaseURL / 模型名），存于 localStorage
- GitHub Actions 自动部署到 gh-pages
- Vitest 单元测试覆盖 settings / state / prompts / routes / graph / hook

### Removed
- 全部 Python 源码（langgraph_essay_grading、langchain_agent、FastAPI 服务层）
- Python Notebook、pyproject.toml、uv.lock、.venv
- .env（API Key 改由前端用户配置）
```

- [ ] **Step 2: 提交**

```bash
git add CHANGELOG.md
git commit -m "docs: 记录 TypeScript 重构与 GH Pages 部署变更"
```

---

## Task 23: 改写 CLAUDE.md 为 TS 规范

**Files:**
- Modify: `CLAUDE.md`（完全替换）

- [ ] **Step 1: 写入新 CLAUDE.md**

```markdown
# TypeScript 项目开发规范

> 面向人类开发者与 AI 编程助手（Claude Code）。

## 🤖 AI 助手行为准则

### 环境与依赖管理
- **包管理**：使用 `npm`（已配 `npmmirror` 镜像），新增依赖 `npm install <pkg>`，禁止手动改 `package.json`
- **代码目录**：业务代码放 `src/`，测试放 `tests/`，二者结构镜像
- **环境同步**：`package.json` 修改后必须 `npm install`

### 质量门禁
- **类型检查**：每次修改后跑 `npx tsc --noEmit`
- **Lint**：完成后跑 `npm run lint`
- **测试**：完成后跑 `npm test`；失败重试最多 3 次，仍失败则报告用户

### 操作限制
- **Git**：可 `git add` / `git commit` / `git push`；force push 需确认
- **删除**：删除文件前必须确认

## 🛠 环境与工具

- **Node**：20+
- **包管理**：npm
- **构建**：Vite 5
- **开发工具**：ESLint（lint）、Prettier（format）、TypeScript（类型）、Vitest（测试）

## 📂 项目结构

```
project-root/
├── src/
│   ├── components/         # 展示型 React 组件
│   ├── pages/              # 路由页面
│   ├── workflow/           # LangGraph 工作流（state / nodes / routes / graph / llm / prompts）
│   ├── hooks/              # 自定义 React hooks
│   ├── lib/                # 通用工具
│   ├── styles/             # 全局 CSS
│   ├── App.tsx
│   └── main.tsx
├── tests/                  # 结构镜像 src/
├── .github/workflows/      # CI/CD
├── index.html              # Vite 入口
├── vite.config.ts
├── vitest.config.ts
├── tsconfig.json
├── package.json
└── README.md
```

### 导入规范
- 使用**绝对导入**：`import { ... } from "src/workflow/graph"`
- 修改导出需更新对应 `__all__`（不适用，本项目无 barrel export）

## 📝 代码规范

### 风格
- 缩进 2 空格，行长 ≤100，文件结尾 1 空行
- 单引号优先（如项目配置），或遵循 Prettier 默认
- 函数组件用箭头函数

### 命名
| 类型 | 规范 | 示例 |
| :--- | :--- | :--- |
| 变量/函数 | `camelCase` | `getUserName` |
| 组件/类型/类 | `PascalCase` | `GradingPage`、`ScoreCard` |
| 常量 | `UPPER_SNAKE_CASE` | `MAX_RETRY_COUNT` |
| 私有 | `_` 前缀 | `_internalCache` |

### 函数设计
- 长度控制在 50 行内
- 公共函数 100% 类型注解（启用 `strict`）
- 组件 Props 用 `type Props = { ... }` 显式定义

### 异常处理
- **禁止**裸露 `catch {}` 或吞掉错误
- 异步错误向上抛，由调用方决定如何展示（toast / alert / 卡片内联）

### 安全
- 严禁硬编码密钥 / Token / 连接串
- LLM API Key 必须由用户在设置页输入并存于 localStorage
- CI 不存任何敏感信息（GH Pages 部署无需 secret）

### 文档
- 模块、组件、公共函数推荐写 JSDoc 或简短注释

### 代码注释
- 所有代码注释使用**中文**
- 注释应清晰说明代码的功能和逻辑
- 禁止无意义注释

## 🤖 AI 助手通用行为准则

### 1. Coding 前先思考
- 在实现之前：明确假设，不确定时主动询问
- 如有多种解释，呈现出来而非沉默选择

### 2. 简洁优先
- 不添加超出需求的功能
- 不为单次使用的代码创建抽象
- 不为不可能的场景添加错误处理

### 3. 精准修改
- 只改必须改的
- 不"优化"相邻的代码或格式
- 移除因本次修改而变得未使用的 import / 变量 / 函数

### 4. 目标驱动执行
- 将任务转化为可验证的目标
- 对于多步骤任务，陈述简要计划

## 📦 Git 提交规范

**格式**：`<type>: <描述>`（中文）

| Type | 说明 |
| :--- | :--- |
| `feat` | 新功能 |
| `fix` | 修复 Bug |
| `docs` | 文档更新 |
| `style` | 格式调整 |
| `refactor` | 重构 |
| `test` | 测试相关 |
| `chore` | 工具变动 |

描述使用中文，简洁说明本次提交做了什么（不超过 50 字）。

### 变更记录
- 代码提交前，必须在 `CHANGELOG.md` 中记录本次修改的内容
- 使用 `[Unreleased]` 标签记录未发布的变更

## 📎 常用命令

```bash
# 安装依赖
npm install

# 开发
npm run dev              # 启动 Vite dev server
npm run build            # 类型检查 + 产出 dist/
npm run preview          # 预览构建产物

# 测试与质量
npm test                 # 跑一次 Vitest
npm run test:watch       # 监听模式
npm run lint             # ESLint
npm run format           # Prettier
npx tsc --noEmit         # 仅类型检查
```
```

- [ ] **Step 2: 提交**

```bash
git add CLAUDE.md
git commit -m "docs: 改写 CLAUDE.md 为 TypeScript 项目规范"
```

---

## Task 24: 改写 README

**Files:**
- Modify: `README.md`（完全替换）

- [ ] **Step 1: 写入新 README.md**

```markdown
# 高考作文评分系统 | Gaokao Essay Grading System

基于 LangGraph 的多维度智能评分系统，对高考作文进行审题立意、论据分析、结构评估、语言文采四维度评分。**纯前端实现，部署在 GitHub Pages**。

![前端界面展示](./page.png)

## 功能特性

### 四维度评分体系

| 维度 | 说明 | 权重 |
|------|------|------|
| 审题立意 | 评估是否准确理解题目，主题是否深刻 | 30% |
| 论据分析 | 评估论据的质量、丰富度与论证深度 | 20% |
| 结构评估 | 评估文章逻辑层次与段落衔接 | 20% |
| 语言文采 | 评估用词、句式、修辞与文采 | 30% |

### 条件短路机制

当「审题立意」得分 ≤ 0.5 时，系统直接跳到最后综合评分，跳过其余三个维度的评估——确保跑题作文不会被过度评分。

### 并行评估

当审题通过时，论据、结构、语言三个维度并行独立评估，效率更高。

### 流式体验

每完成一个维度评分，前端立即更新对应卡片，无需等待全部完成。

## 快速开始（本地开发）

```bash
npm install
npm run dev          # 访问 http://localhost:5173
```

## 使用流程

1. 打开页面，右上角点「设置」
2. 填入你的 LLM API Key、BaseURL、模型名（默认已预填百灵配置）
3. 点「测试连接」验证配置正确
4. 点「保存」返回主页
5. 输入作文题目与内容，点「开始评分」

> **API Key 存于浏览器 localStorage**，不进任何后端。建议使用额度受限的次级 Key。

## 技术架构

```
浏览器 SPA
  ├─ React (UI)
  ├─ React Router (路由)
  ├─ @langchain/langgraph (工作流编排)
  ├─ @langchain/openai (LLM 客户端)
  └─ localStorage (API Key 存储)
       │
       │ HTTPS 直连（无中间代理）
       ▼
   LLM Provider (百灵 / DeepSeek / 智谱 / OpenAI 等 OpenAI 兼容 API)
```

## 部署到 GitHub Pages

1. 在 GitHub 仓库 Settings → Pages → Source 选「GitHub Actions」
2. 推 `main` 分支即触发自动构建与部署
3. 访问 `https://<user>.github.io/<repo>`

构建产物在 `dist/`，由 `actions/deploy-pages` 上传。

## 支持的 LLM Provider

任何 OpenAI 兼容协议的 API 都可以。已在以下 provider 验证：

- 百灵（默认）
- DeepSeek
- 智谱 GLM
- 美团 LongCat
- 魔塔、硅基流动
- 自建 Ollama

**注意**：浏览器直接请求 LLM API，依赖 provider 已配置 CORS 允许 `github.io` 域名。百灵已支持。

## 开发

```bash
npm test              # 跑 Vitest
npm run lint          # ESLint
npm run build         # 类型检查 + Vite 构建
```

## 安全提示

- ⚠️ API Key 一旦填入，任何能访问此浏览器的人都能看到
- ⚠️ 部署到公开 GH Pages 后，访客使用自己的 Key 评分；但若 Key 泄露到日志或源码，会被盗刷
- ✅ Key 仅存 localStorage，不进 git 仓库
- ✅ 建议在 LLM provider 端设置月度额度上限

## License

MIT
```

- [ ] **Step 2: 提交**

```bash
git add README.md
git commit -m "docs: 改写 README 为 TypeScript + GH Pages 版本"
```

---

## Task 25: 全量验证

**Files:** 无新增

- [ ] **Step 1: 跑类型检查**

```bash
cd /home/cooper/githubProjects/langgraph-essay-grading
npx tsc --noEmit
```

预期：无错误。

- [ ] **Step 2: 跑所有测试**

```bash
npm test
```

预期：所有用例通过。

- [ ] **Step 3: 跑 lint**

```bash
npm run lint
```

预期：无错误。

- [ ] **Step 4: 完整构建**

```bash
npm run build
```

预期：产出 `dist/index.html`、`dist/assets/*.js`、`dist/assets/*.css`，无错误。

- [ ] **Step 5: 检查 dist 产物**

```bash
ls -la dist/ dist/assets/
```

预期：HTML、JS、CSS 都在。

- [ ] **Step 6: 验证无 LLM Key 泄露到仓库**

```bash
git grep -iE 'sk-[a-zA-Z0-9]{20,}|api[_-]?key.*=.*[a-zA-Z0-9]{20,}' || echo "OK: 无 Key 泄露"
```

预期：`OK: 无 Key 泄露`。

- [ ] **Step 7: 启动 dev server 做一次端到端 smoke**

```bash
timeout 10 npm run dev &
sleep 6
curl -sf http://localhost:5173/ | head -c 200
kill %1
```

预期：返回 HTML 含 root 容器。

- [ ] **Step 8: 提交（如有自动生成的格式修复）**

```bash
git status --short
# 若有变更：
git add -A
git commit -m "chore: 全量验证后格式统一"
```

---

## 完成检查清单

- [ ] 所有 25 个任务的 checkbox 全部勾选
- [ ] `npm test` 全绿
- [ ] `npx tsc --noEmit` 无错
- [ ] `npm run lint` 无错
- [ ] `npm run build` 成功
- [ ] `dist/` 产物存在
- [ ] git 仓库无任何 LLM Key 痕迹
- [ ] 25 次提交全部 push 到 main（最后一次手动 `git push` 触发 GH Actions 部署）
- [ ] 合并后访问 GH Pages URL 可见主页
- [ ] 在浏览器设置页填入有效 Key 后可完成一次完整评分
