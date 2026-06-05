# 高考作文评分系统：Python → TypeScript 重构与 GitHub Pages 部署

**日期**：2026-06-05
**状态**：待用户审阅
**目标**：将现有 Python + LangGraph + FastAPI 实现的「高考作文评分系统」重写为 TypeScript + React + Vite 单页应用，并部署到 GitHub Pages。

---

## 1. 背景与动机

现有系统是单仓库 Python 项目：

- 后端：FastAPI + LangGraph 编排的 4 节点评分图（审题立意 / 论据分析 / 结构评估 / 语言文采）+ 条件短路 + 并行扇出 + SSE 流式输出
- LLM：通过 `langchain_agent/utils/llm_factory.py` 切换百灵、智谱、DeepSeek、美团 LongCat、Ollama、NVIDIA 等多个 provider
- 前端：`src/static/index.html` 单文件 HTML + 内联 CSS + 原生 JS

**重构目标**：

1. 整个代码库（Python）改写为 TypeScript
2. 部署到 GitHub Pages（静态托管）

**关键约束**：

- GitHub Pages 仅支持静态文件托管，无后端、无服务端进程
- LLM API Key 绝不能进仓库或前端代码
- 必须保留现有「条件短路 + 并行评分 + 流式体验」业务逻辑

---

## 2. 架构总览

### 2.1 部署形态：纯前端 + 用户自带 Key

```
┌─────────────────────────────────────────────────────────────┐
│                GitHub Pages (静态托管)                       │
│                                                              │
│   ┌──────────────────┐      ┌─────────────────────────┐    │
│   │  React SPA       │      │  @langchain/langgraph   │    │
│   │  GradingPage     │◀────▶│  评分工作流 (浏览器内)   │    │
│   │  SettingsPage    │      │                         │    │
│   └──────────────────┘      └──────────┬──────────────┘    │
│           │                             │                    │
│           │  API Key / BaseURL /        │                    │
│           │  ModelName                  │                    │
│           ▼                             ▼                    │
│     localStorage              HTTPS 直连 LLM Provider        │
│     (用户自带 Key)            (百灵 / OpenAI 兼容)            │
└─────────────────────────────────────────────────────────────┘
```

**为什么选这条路**：

- 完全契合 GitHub Pages 静态托管能力
- 0 服务端成本、0 部署复杂度
- 用户自带 Key 解决「Key 不能进仓库」的安全问题
- CORS 风险：依赖 LLM provider 配置（百灵需支持 github.io 域名的 CORS）

### 2.2 技术选型

| 维度 | 选择 | 理由 |
|------|------|------|
| 语言 | TypeScript（strict） | 用户指定 |
| 构建工具 | Vite | 静态产物、配置简单、生态成熟 |
| UI 框架 | React 18 + React Router | 与现有 DOM/事件模型最接近、迁移成本低 |
| 工作流引擎 | `@langchain/langgraph`（TS 版） | 1:1 复用 Python 的图结构与节点设计 |
| LLM 客户端 | `@langchain/openai`（ChatOpenAI，OpenAI 兼容协议） | 百灵等多家 provider 兼容 OpenAI 协议 |
| Schema | Zod | TS 原生、`@langchain/langgraph` 直接支持 `.withStructuredOutput(zodSchema)` |
| Lint / 格式 | ESLint + Prettier | 业界标准 |
| 测试 | Vitest | 与 Vite 集成最快 |
| 部署 | GitHub Actions + `actions/deploy-pages` | 推送 main 自动部署 |
| 默认 Provider | 百灵（`LING_BASEURL` / `LING_MODEL_NAME`） | 与用户现有 `.env` 配置一致 |

### 2.3 不引入的东西

- **不引入**后端框架（FastAPI / Hono / Express 等）
- **不引入**状态管理库（Redux / Zustand）——`useState` + `useEffect` 足够
- **不引入** UI 组件库（Ant Design / Material UI）——保留原版视觉、用原生 CSS
- **不引入** SSR / SSG（Next.js / Astro）——纯 SPA 即可
- **不引入** LangGraph 之外的 workflow 库

---

## 3. 项目结构

```
langgraph-essay-grading/
├── .github/workflows/deploy.yml    # GH Actions: push main → build → deploy gh-pages
├── public/                          # favicon 等静态资源
├── src/
│   ├── main.tsx                     # React 入口
│   ├── App.tsx                      # 路由
│   ├── pages/
│   │   ├── GradingPage.tsx          # 评分主页（原 index.html 主体）
│   │   └── SettingsPage.tsx         # API Key / BaseURL / 模型名设置
│   ├── workflow/
│   │   ├── state.ts                 # EssayState 类型 + Zod ScoreDetail
│   │   ├── config.ts                # 权重、阈值、节点名常量
│   │   ├── prompts.ts               # 4 个维度提示词 + buildPrompt
│   │   ├── llm.ts                   # ChatOpenAI 工厂（从 localStorage 读）
│   │   ├── nodes.ts                 # 4 个评分节点（TS 版）
│   │   ├── routes.ts                # routeRelevance 路由函数
│   │   └── graph.ts                 # StateGraph 构建与编译
│   ├── components/
│   │   ├── ScoreCard.tsx
│   │   ├── SkeletonCard.tsx
│   │   └── FinalScoreCard.tsx
│   ├── hooks/
│   │   └── useGradingStream.ts      # 订阅 graph.stream() 事件
│   ├── lib/
│   │   └── settings.ts              # localStorage 读写
│   ├── styles/
│   │   └── index.css                # 现有 CSS 平移
│   └── types.ts                     # 共享类型
├── tests/
│   └── workflow/
│       ├── graph.test.ts
│       ├── routes.test.ts
│       └── settings.test.ts
├── index.html                       # Vite 入口 HTML
├── vite.config.ts                   # base: './'
├── tsconfig.json                    # strict: true
├── package.json
├── .gitignore                       # 追加 node_modules/ dist/
├── README.md                        # 改写为新项目说明
├── CHANGELOG.md                     # [Unreleased] 记录
├── CLAUDE.md                        # 改写为 TS 项目规范
└── LICENSE
```

**Vite 配置关键项**：

- `base: './'`：兼容 `https://<user>.github.io/<repo>` 子路径
- `build.outDir: 'dist'`
- `build.sourcemap: false`（生产减小体积）

**tsconfig 关键项**：

- `"strict": true`
- `"target": "ES2022"`
- `"module": "ESNext"`、`"moduleResolution": "bundler"`

---

## 4. 评分工作流

### 4.1 State 定义

```ts
// src/workflow/state.ts
import { z } from "zod";
import { Annotation } from "@langchain/langgraph";

export const ScoreDetail = z.object({
  score: z.number().min(0).max(1),
  reason: z.string(),
});
export type ScoreDetail = z.infer<typeof ScoreDetail>;

export const EssayState = Annotation.Root({
  topic:       Annotation<string>(),
  essay:       Annotation<string>(),
  relevance:   Annotation<ScoreDetail>(),   // 审题立意
  evidence:    Annotation<ScoreDetail>(),   // 论据分析
  structure:   Annotation<ScoreDetail>(),   // 结构评估
  expression:  Annotation<ScoreDetail>(),   // 语言文采
  final_score: Annotation<number>(),        // 综合分
});
```

### 4.2 图结构

```
START
  └─→ check_relevance
        ├─ score > 0.5 ─→ fan_out
        │                    ├─→ check_evidence   ─┐
        │                    ├─→ check_structure  ─┼─→ calculate_final_score → END
        │                    └─→ check_expression ─┘
        └─ score ≤ 0.5 ─→ calculate_final_score → END
```

与 Python 版 LangGraph 图 **节点名、边、条件路由完全一致**。

### 4.3 节点实现

```ts
// src/workflow/nodes.ts
import { HumanMessage, SystemMessage } from "@langchain/core/messages";
import { getLLM } from "./llm";
import { ScoreDetail } from "./state";
import { SYSTEM_PROMPT, buildPrompt } from "./prompts";

async function gradeDim(
  state: EssayStateType,
  dim: "relevance" | "evidence" | "structure" | "expression",
  instruction: string
): Promise<Partial<EssayStateType>> {
  const llm = getLLM().withStructuredOutput(ScoreDetail);
  const messages = [
    new SystemMessage(buildPrompt(ScoreDetail) + SYSTEM_PROMPT),
    new HumanMessage(
      `${instruction}\n给出 0 到 1 之间的分数，并说明理由。\n\n题目：${state.topic}\n\n作文：${state.essay}`
    ),
  ];
  return { [dim]: await llm.invoke(messages) } as any;
}

export const check_relevance  = (s) => gradeDim(s, "relevance", "请评估审题立意...");
export const check_evidence   = (s) => gradeDim(s, "evidence",  "请评估论据分析...");
export const check_structure  = (s) => gradeDim(s, "structure", "请评估结构...");
export const check_expression = (s) => gradeDim(s, "expression","请评估语言文采...");

export function calculate_final_score(state: EssayStateType) {
  const final =
    state.relevance.score  * 0.3 +
    state.evidence.score   * 0.2 +
    state.structure.score  * 0.2 +
    state.expression.score * 0.3;
  return { final_score: Math.round(final * 100) / 100 };
}
```

### 4.4 条件路由

```ts
// src/workflow/routes.ts
const RELEVANCE_THRESHOLD = 0.5;

export function routeRelevance(state: EssayStateType):
  "fan_out" | "calculate_final_score" {
  return state.relevance.score > RELEVANCE_THRESHOLD
    ? "fan_out"
    : "calculate_final_score";
}
```

### 4.5 图构建

```ts
// src/workflow/graph.ts
import { StateGraph, START, END } from "@langchain/langgraph";
import { EssayState } from "./state";
import {
  check_relevance, check_evidence, check_structure, check_expression,
  calculate_final_score,
} from "./nodes";
import { routeRelevance } from "./routes";

const fanOut = (_: EssayStateType) => ({});

const workflow = new StateGraph(EssayState)
  .addNode("check_relevance", check_relevance)
  .addNode("fan_out", fanOut)
  .addNode("check_evidence", check_evidence)
  .addNode("check_structure", check_structure)
  .addNode("check_expression", check_expression)
  .addNode("calculate_final_score", calculate_final_score)
  .addEdge(START, "check_relevance")
  .addConditionalEdges("check_relevance", routeRelevance, {
    fan_out: "fan_out",
    calculate_final_score: "calculate_final_score",
  })
  .addEdge("fan_out", "check_evidence")
  .addEdge("fan_out", "check_structure")
  .addEdge("fan_out", "check_expression")
  .addEdge("check_evidence", "calculate_final_score")
  .addEdge("check_structure", "calculate_final_score")
  .addEdge("check_expression", "calculate_final_score")
  .addEdge("calculate_final_score", END);

export const graph = workflow.compile();
```

### 4.6 流式事件订阅

`graph.stream(initialState, { streamMode: "updates" })` 返回 `AsyncIterable<Record<nodeName, update>>`，UI 侧按节点名更新对应卡片：

| 节点 | UI 行为 |
|------|---------|
| `check_relevance` | 立即显示第一张评分卡 + 三个骨架屏占位 |
| `fan_out` | loading 文案切换为「启动并行评分」 |
| `check_evidence` / `check_structure` / `check_expression` | 到达时替换对应骨架屏为评分卡（任意顺序） |
| `calculate_final_score` | 显示最终加权分 |
| 流结束 | loading 文案切为「评分完成」 |

---

## 5. LLM 客户端与设置

### 5.1 LLM 工厂

```ts
// src/workflow/llm.ts
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

懒加载：每次评分前调用，读取最新设置。

### 5.2 设置存储

```ts
// src/lib/settings.ts
const KEY = "grading-settings-v1";

export type Settings = { apiKey: string; baseUrl: string; modelName: string };

export const DEFAULT_SETTINGS: Settings = {
  apiKey: "",
  baseUrl: "https://api.bailing.cn/v1",   // 百灵默认
  modelName: "Ling-2.6-flash",
};

export function loadSettings(): Settings {
  try {
    const raw = localStorage.getItem(KEY);
    return raw ? { ...DEFAULT_SETTINGS, ...JSON.parse(raw) } : DEFAULT_SETTINGS;
  } catch { return DEFAULT_SETTINGS; }
}

export function saveSettings(s: Settings): void {
  localStorage.setItem(KEY, JSON.stringify(s));
}
```

### 5.3 设置页 UX

- 路径 `/settings`，主页右上角齿轮图标入口
- 三个输入框：API Key（`type="password"` 带显示/隐藏切换）、Base URL、模型名
- 占位提示用默认值
- 「测试连接」按钮：调 `llm.invoke([new HumanMessage("hi")])`，2 秒内返回即视为通过
- 保存按钮：写入 localStorage 后跳回主页
- 未设置 `apiKey` 时访问 `/` 重定向到 `/settings`

### 5.4 安全模型

| 风险 | 缓解 |
|------|------|
| API Key 进仓库 | 始终在 localStorage，提交前 grep 校验 |
| CORS 阻挡 | README 文档说明百灵 CORS 要求；用户换 provider 需自验 |
| XSS 盗 Key | 仅 react + 静态渲染，不引入 `dangerouslySetInnerHTML`；依赖锁版本 |
| 滥用 / 盗刷 | README 建议使用次级 Key + provider 端设置费率上限 |

### 5.5 错误处理

| 场景 | 表现 |
|------|------|
| 网络中断 / 超时 | 单维度卡片显示「失败：xxx」+ 重试按钮；不阻塞其他维度 |
| 401 / 403 | 全局 toast「API Key 无效，请到设置页检查」 |
| CORS / 5xx | 卡片显示具体错误信息 |
| LLM 返回非 JSON | `.withStructuredOutput` 自动重试一次，仍失败则卡片报错 |

---

## 6. UI 组件

### 6.1 组件树

```
<App>
  <Routes>
    <Route path="/"         element={<GradingPage />} />
    <Route path="/settings" element={<SettingsPage />} />
  </Routes>
</App>

<GradingPage>
  <Header>                  // 标题 + 齿轮按钮
  <FormSection>             // 题目输入 + 作文 textarea + 提交按钮
  <LoadingBar />            // 三点动效 + 阶段文案
  <ResultsSection>          // 评分卡 grid + 总分卡
    <ScoreCard /> × N
    <SkeletonCard /> × N
    <FinalScoreCard />
  </ResultsSection>
</GradingPage>

<SettingsPage>
  <FormSection>             // Key / BaseURL / ModelName
  <TestButton />
  <SaveButton />
</SettingsPage>
```

### 6.2 核心 Hook

```ts
// src/hooks/useGradingStream.ts
import { useState, useCallback } from "react";
import { graph } from "../workflow/graph";

export type StreamEvent = { node: string; update: Record<string, any> };

export function useGradingStream() {
  const [events, setEvents] = useState<StreamEvent[]>([]);
  const [done, setDone] = useState(false);
  const [running, setRunning] = useState(false);

  const run = useCallback(async (state: { topic: string; essay: string }) => {
    setEvents([]); setDone(false); setRunning(true);
    try {
      const stream = await graph.stream(state, { streamMode: "updates" });
      for await (const event of stream) {
        for (const [node, update] of Object.entries(event)) {
          setEvents(prev => [...prev, { node, update }]);
        }
      }
    } finally {
      setDone(true); setRunning(false);
    }
  }, []);

  return { events, done, running, run };
}
```

### 6.3 视觉与 CSS

- 保留 `src/static/index.html` 中的全部 CSS（迁移到 `src/styles/index.css`）
- 保持原有配色、动画、响应式断点
- 不用 CSS 框架、不用 CSS-in-JS

---

## 7. 测试

| 范围 | 工具 | 覆盖目标 |
|------|------|---------|
| `routeRelevance` 短路逻辑 | Vitest | 边界值 0.5、0.500001、0、1 |
| `buildPrompt` 提示词 | Vitest | 包含 schema 字段名、schema 定义块 |
| `loadSettings` / `saveSettings` | Vitest | 空值、缺字段、JSON 损坏 |
| 工作流图连通性 | Vitest | mock ChatOpenAI 验证边触发顺序、并行分支 |
| **不**做 | — | 组件快照测试、E2E 浏览器测试 |

Mock LLM 策略：`vi.mock("@langchain/openai")` 替换为返回固定 `ScoreDetail` 的 stub。

---

## 8. 部署

### 8.1 GitHub Actions

`.github/workflows/deploy.yml`：

```yaml
name: Deploy to GitHub Pages
on:
  push: { branches: [main] }
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
        with: { node-version: 20, cache: npm }
      - run: npm ci
      - run: npm run build
      - uses: actions/configure-pages@v5
      - uses: actions/upload-pages-artifact@v3
        with: { path: dist }
      - id: deployment
        uses: actions/deploy-pages@v4
```

### 8.2 仓库设置

- Settings → Pages → Source 选「GitHub Actions」
- 首次合并后访问 `https://<user>.github.io/<repo>`

### 8.3 本地预览

```bash
npm run dev          # vite dev server，localhost:5173
npm run build        # 产出 dist/
npm run preview      # 预览构建产物
```

---

## 9. Python 旧代码处置

| 路径 | 处置 |
|------|------|
| `langgraph_essay_grading/` | 删除 |
| `langchain_agent/` | 删除 |
| `src/`（旧 web 层） | 删除 |
| `main.py` | 删除 |
| `pyproject.toml`、`uv.lock` | 删除 |
| `.venv/`、`.python-version` | 删除 |
| `.env` | 删除（Key 改由用户在前端填入） |
| `.env.example` | 删除 |
| `pyproject-editable-install.md` | 删除 |
| `langgraph_essay_grading/docs/essay_grading_system_langgraph.ipynb` | 删除 |
| `src/static/index.html` | 内容迁移到新前端 |
| `README.md` | 改写为新项目说明 |
| `LICENSE` | 保留 |
| `.gitignore` | 追加 `node_modules/`、`dist/`、`coverage/` |
| `CHANGELOG.md` | 在 `[Unreleased]` 记录本次重构 |
| `CLAUDE.md` | 改写为 TS 项目规范（去掉 Python 特定条目；新增 npm/vite/eslint/vitest 流程） |
| `page.png` | 保留作为 README 配图（可换成新截图） |

---

## 10. 风险与缓解

| 风险 | 缓解 |
|------|------|
| 百灵 API 未配置 CORS for github.io | 首次发布后用 `curl` 自验；README 列出 CORS 不通过时的备选 provider |
| LLM 响应慢 / 超时 | 单维度超时独立处理，不阻塞其他维度；UI 显示重试按钮 |
| 用户误把 Key 提交进仓库 | 提交前在 `.gitignore` 中忽略 `.env`；`actions/checkout` 不做额外事；CI 加 `grep -r "sk-" .` 防御（可选） |
| LangGraph TS 版 API 变更 | 锁定 `@langchain/langgraph` 主版本号；遇到 breaking change 在 PR 中标注 |
| LLM 返回的 JSON 偶尔缺字段 | Zod 默认严格模式解析失败 → 卡片显示「返回格式异常」+ 重试 |
| 旧 README/CLAUDE.md 误导新用户 | 与代码一起强制重写为 TS 版本 |

---

## 11. 验收标准

- [ ] `npm run build` 成功，产物在 `dist/`
- [ ] `npm run test` 全部通过
- [ ] `npm run lint` 与 `tsc --noEmit` 无错误
- [ ] 在 `localhost:5173` 输入有效 Key 后能完整跑出 4 维度评分 + 总分
- [ ] 故意填错 Key → 出现「Key 无效」提示
- [ ] 故意写跑题作文（让审题 < 0.5）→ 跳过其他三维、直接显示总分
- [ ] GitHub Actions 部署成功，可通过 `https://<user>.github.io/<repo>` 访问
- [ ] 浏览器 DevTools Network 面板确认请求直接发到 LLM provider（无中间代理）
- [ ] 旧 Python 文件全部从仓库删除
- [ ] 仓库无任何 LLM API Key 痕迹

---

## 12. 后续可扩展项（本次不实现）

- 多 provider 下拉切换（本次固定单 provider）
- LLM 响应 SSE 真正流式（chunk 级）
- 评分历史持久化（IndexedDB）
- 评分维度权重可视化调节
- 多语言界面（i18n）
- 暗色模式
- PWA 离线能力
