# 高考作文模式（7 维度 + w.md 评分标准）

**日期**：2026-06-06
**状态**：待用户审阅
**目标**：在首页（GradingPage）增加「高考作文模式」切换。开启后，评分工作流从现有 4 维度升级为 7 维度，全面覆盖 `w.md` 的「基础等级 + 发展等级 + 卷面」评分规则；关闭后回退到现有 4 维度行为。

---

## 1. 背景与动机

当前 GradingPage 的 4 维度（审题立意 / 论据 / 结构 / 语言）由 `src/workflow/nodes.ts` 中的 `DIM_INSTRUCTIONS` 定义，仅是抽象的「四把尺」，没有显式对齐教育部考试中心的高考语文作文评分细则。

`w.md` 是用户提供的官方评分标准，结构如下：

- **基础等级** 40 分
  - 内容 20 分：题意 / 中心 / 内容 / 思想 / 感情
  - 表达 20 分：结构 / 语言 / 文体 / 卷面
- **发展等级** 20 分
  - 特征 20 分：深刻 / 丰富 / 有文采 / 有创意（4 类 16 点）
- **扣分细则**：错别字（1 字 1 分）、标点（3 处以上）、字数（每少 50 字 -1）、无标题（-2）
- **残篇评定**：400 字以上正常评、400 字以下 20 分封顶、200 字以下 10 分封顶

把 w.md 内化进系统有两个收益：

1. 评分标准与真实阅卷场对齐，输出更有公信力
2. 维度更细（7 个），让用户看到自己的作文在每个细分维度上的具体强弱

**关键约束**：

- 总分仍以 1.00 为满分（用户明确要求）
- 标准模式不破坏（向后兼容 4 维度 + 0.3/0.2/0.2/0.3 权重）
- 状态字段命名不污染现有 `relevance / evidence / structure / expression`，gaokao 模式新增 4 个独立字段
- 所有改动必须局部化：评分卡组件 `ScoreCard` 不动；只动 `GradingPage / FormSection / workflow / 新增 ModeToggle`

---

## 2. 架构

```
                    ┌──────────────────────────────────┐
                    │      localStorage                │
                    │   grading-mode-v1: "gaokao"     │
                    └──────────────┬───────────────────┘
                                   │ 启动时读取
                                   ▼
┌─────────────────────────────────────────────────────────────────┐
│                       GradingPage                                │
│   const [mode, setMode] = useState<Mode>(loadMode())             │
│                                                                  │
│   ┌──────────────────────┐    segmented control                  │
│   │  ModeToggle          │◀──「标准模式」「高考模式」             │
│   └──────────────────────┘                                       │
│                                                                  │
│   handleSubmit()  →  run({ mode, topic, essay })                 │
└──────────────────────────┬───────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                  useGradingStream                                 │
│   根据 mode 选 graph:                                             │
│     standardGraph (4 维)   /   gaokaoGraph (7 维)                 │
└──────────────────────────┬───────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│              LangGraph workflow (按 mode 选)                      │
│                                                                  │
│  standard:                                                        │
│    relevance → 短路                                              │
│      ├ 跑题 → calculate_final_score (4 维加权)                   │
│      └ 切题 → fan_out → 3 维并行 → calculate_final_score         │
│                                                                  │
│  gaokao:                                                          │
│    relevance → 短路                                              │
│      ├ 跑题 → calculate_final_score (7 维加权)                   │
│      └ 切题 → fan_out → 6 维并行 → calculate_final_score         │
└─────────────────────────────────────────────────────────────────┘
```

**关键决策**：

- **不动现有字段名**：`EssayState` 保留 `relevance / evidence / structure / expression`；gaokao 新增 `content / depth / novelty / formatting`
- **两个 graph 编译两份**：`standardGraph` 与 `gaokaoGraph` 在 `graph.ts` 编译，导出 `getGraph(mode)` selector
- **score 区间统一**：所有维度都输出 0-1，最终 `calculate_final_score` 用 `Math.round(final * 100) / 100` 保留两位小数
- **prompt 切换**：系统 prompt 拆为 `STANDARD_SYSTEM_PROMPT` 与 `GAOKAO_SYSTEM_PROMPT`，后者内化 w.md 的五等评分 + 16 点特征 + 扣分细则

---

## 3. 7 维度拆解（高考模式）

| # | 中文名 | 节点名 | 对应 w.md | 评估要点 |
| --- | --- | --- | --- | --- |
| 1 | 审题立意 | `check_relevance` | 基础-内容 | 题意 / 中心 / 思想 / 感情 |
| 2 | 内容论据 | `check_content` | 基础-内容 | 内容是否充实 / 材料 / 论据 |
| 3 | 篇章结构 | `check_structure` | 基础-表达 | 段落 / 层次 / 过渡 / 衔接 |
| 4 | 语言文采 | `check_expression` | 基础-表达 + 发展-文采 | 用词 / 句式 / 修辞 / 文句表现力 |
| 5 | 思想深度 | `check_depth` | 发展-深刻 | 透过现象看本质 / 揭示因果 / 启发性 |
| 6 | 创新创意 | `check_novelty` | 发展-创意 | 见解新颖 / 构思精巧 / 推理想象独到 / 个性 |
| 7 | 卷面格式 | `check_formatting` | 扣分细则 | 错别字 / 标点 / 字数 / 标题 |

**权重分配**（用户决策：7 维度等分）：

```
WEIGHT_PER_DIM = 1 / 7 ≈ 0.142857
sum = 7 × (1/7) = 1.00
```

`calculate_final_score` 按 `getWeights(mode)` 选权重表，公式保持不变。

---

## 4. 组件与数据流

### 4.1 新增 / 修改文件

| 文件 | 类型 | 作用 |
| --- | --- | --- |
| `src/lib/mode-storage.ts` | 新增 | 读 / 写 `grading-mode-v1` localStorage 键，默认 `"gaokao"`，导出 `loadMode()` / `saveMode()` |
| `src/workflow/dimensions.ts` | 新增 | 导出 `Mode` 类型 (`"standard" \| "gaokao"`)、`STANDARD_DIMS`、`GAOKAO_DIMS`、`getDimensions(mode)`、`getWeights(mode)` |
| `tests/workflow/dimensions.test.ts` | 新增 | 单元测试两种模式的权重和、维度顺序、节点名映射 |
| `src/workflow/prompts.ts` | 修改 | `SYSTEM_PROMPT` 拆为 `STANDARD_SYSTEM_PROMPT` 与 `GAOKAO_SYSTEM_PROMPT`，后者把 w.md 的五等评分、16 点特征、扣分细则写进系统提示 |
| `src/workflow/config.ts` | 修改 | `NODE_NAMES` 扩展：`CONTENT / DEPTH / NOVELTY / FORMATTING` 四个新节点常量；`WEIGHT_*` 改由 `dimensions.ts` 集中管理 |
| `src/workflow/nodes.ts` | 修改 | `DIM_INSTRUCTIONS` 改为 `getInstructions(mode, dim)`；每个 gaokao 维度对应一段完整 w.md 描述 |
| `src/workflow/graph.ts` | 修改 | 编译 `standardGraph` 与 `gaokaoGraph`，导出 `getGraph(mode)`；`calculate_final_score` 改为读 `getWeights(mode)` |
| `src/components/ModeToggle.tsx` | 新增 | segmented 控件：「标准模式 / 高考模式」两段式 pill 按钮，宣纸 + 朱砂风格 |
| `src/styles/index.css` | 修改 | 新增 `.mode-toggle`、`.mode-toggle-pill`、`.mode-toggle-thumb` 等样式 |
| `src/components/FormSection.tsx` | 修改 | 顶部插入 `ModeToggle`；新增 `mode` 与 `onModeChange` props |
| `src/pages/GradingPage.tsx` | 修改 | 维护 `mode` state、`useEffect` 持久化；`run()` 传 `mode`；按 mode 决定展示哪些 `ScoreCard` |
| `src/hooks/useGradingStream.ts` | 修改 | `run` 接收 `mode`，内部调 `getGraph(mode).stream(...)` |
| `src/components/ScoreCard.tsx` | 不动 | 通用卡，标题由调用方传入 |
| `tests/pages/GradingPage.test.tsx` | 修改 | 新增 case：默认 mode = gaokao、切换 mode 后 graph 选对、模式持久化 |
| `tests/lib/mode-storage.test.ts` | 新增 | localStorage 读写 / 非法值 / 抛错的兜底 |
| `CHANGELOG.md` | 修改 | `[Unreleased]` 下记两条：Added 高考模式、Changed 默认模式 |
| `README.md` | 修改 | 四维度表扩展为七维度表，新增模式说明 |

### 4.2 数据流（Gaokao 模式为例）

```
用户点「高考模式」segmented
    │
    ▼
FormSection.onModeChange("gaokao")
    │
    ▼
GradingPage.setMode("gaokao")
    ├─ useEffect → saveMode("gaokao")  (localStorage)
    └─ setEvents([])  (避免上一次结果残留)
    
用户点「开始评分」
    │
    ▼
handleSubmit(topic, essay)
    ├─ exhausted? return
    ├─ increment()
    └─ run({ mode, topic, essay })
         │
         ▼
    useGradingStream.run
         ├─ getGraph(mode)  // standardGraph / gaokaoGraph
         └─ for await event of stream:
              setEvents(prev => [...prev, event])
                 │
                 ▼
            GradingPage 渲染层
              ├─ 命中 gaokao 节点 → 渲染 7 张 ScoreCard
              └─ 命中 calculate_final_score → 渲染 FinalScoreCard (1.00 满分)
```

### 4.3 UI 视觉规范

**ModeToggle**（FormSection 顶部、题目前）：

```
┌──────────────────────────────────────────────────────┐
│  评分模式:  [ 标准模式 ]  [● 高考模式 ]                │
│              ─────────   ────────────                 │
│              (灰墨)       (朱砂下划线 + 朱砂字)        │
└──────────────────────────────────────────────────────┘
```

- 复用现有 `--ink` `--vermillion` `--paper` `--line-soft` 令牌
- 切换有过渡动画（朱砂下划线滑动 0.2s）
- 在 `disabled` 时（评分中）置灰、不响应点击

**ScoreCard 列表**：

- 标准模式：2 列 grid，4 张卡
- 高考模式：2 列 grid，6 张并排卡 + 第 7 张「卷面格式」单独一行（`grid-column: 1 / -1`），再下接 FinalScoreCard

**FinalScoreCard**：保持「满分 1.00」字样不变，2 种模式都一样。

---

## 5. 错误处理、测试、迁移

### 5.1 错误处理

| 场景 | 行为 |
| --- | --- |
| `localStorage` 不可用 / 抛错 | `loadMode()` 捕获并返回默认 `"gaokao"`，不抛到 UI；`saveMode()` 同样 try/catch 静默失败 |
| 存储的 mode 值不在枚举内（如 `"foo"`） | 视为无效值，回退 `"gaokao"`，并 `console.warn` 一次 |
| 模式切换时上一次评分未结束 | 不打断当前 `run`；下一次提交才用新 mode；切换按钮在 `running` 时 `disabled` |
| 切换后旧 events 未清空 | 切 mode 时 `setEvents([])`，避免高/低维度卡残留造成视觉错位 |
| 维度节点报错（LLM 失败） | 与现有 `alert(\`评分请求失败: ${err.message}\`)` 一致，节点失败向上抛；并行节点相互独立，单点失败不影响其他维度 |
| 跑题短路（relevance ≤ 0.5） | gaokao 模式下同样短路，6 个并行维度全部跳过；与现有逻辑共用 `RELEVANCE_THRESHOLD = 0.5` |
| Gaokao 模式下维度定义缺失 / 配置 bug | 启动时 `getDimensions("gaokao")` 维度数为 7、权重和为 1；不满足时单元测试失败，构建期拦截 |

### 5.2 测试

**单元测试**（新增 `tests/workflow/dimensions.test.ts`）：

- `getDimensions("standard")` 长度 = 4，权重和 = 1
- `getDimensions("gaokao")` 长度 = 7，权重和 = 1
- 每个维度的 `node` 名唯一、不与其它模式冲突
- 节点名 → 中文标签映射完整、无 undefined

**单元测试**（新增 `tests/lib/mode-storage.test.ts`）：

- 默认值 = `"gaokao"`
- `saveMode("standard")` 后 `loadMode()` 返回 `"standard"`
- 注入非法值后 `loadMode()` 回退 `"gaokao"` 并 warn
- localStorage 抛错时不抛到调用方

**集成测试**（修改 `tests/pages/GradingPage.test.tsx`）：

- 默认渲染时 ModeToggle 选中「高考模式」
- 点「标准模式」segmented 后，下次 `run` 调用的是 `standardGraph`（mock 出两个 graph 的 `stream`，断言调用次数或入参 mode）
- 点「高考模式」后下次 run 调用 `gaokaoGraph`
- 模式选择写入 `localStorage` 键 `grading-mode-v1`

**测试覆盖度目标**：所有新模块 ≥ 80%。

### 5.3 迁移 / 影响面

- **不破坏现有 standard 模式**：4 维度名（`relevance/evidence/structure/expression`）保留，权重 0.3/0.2/0.2/0.3 不变
- **state schema 扩展**：gaokao 模式新增 4 个字段（`content / depth / novelty / formatting`），standard 模式不写这些字段，`Annotation` 默认可选，无向后兼容问题
- **events 流**：前端按 `node` 名分发，不依赖 state schema 字段名
- **CHANGELOG.md**：在 `[Unreleased]` 下记「Added: 高考作文模式（7 维度 + w.md 评分标准）」与「Changed: 默认评分模式从标准改为高考」
- **README.md**：四维度表扩展为七维度表，新增「标准模式 / 高考模式」段落

### 5.4 不做（YAGNI）

- ❌ 不做模式历史的「最近一次评分用了什么 mode」记录
- ❌ 不做模式相关的配额差异（2 种模式都扣 1 次）
- ❌ 不做模式快捷键 / URL 参数 / 深链接
- ❌ 不做「标准 / 高考」之外的第三种模式
- ❌ 不改 `FinalScoreCard` 文案「满分 1.00」（两种模式都适用）

---

## 6. 验收清单

- [ ] 首页加载时默认 mode = `gaokao`，ModeToggle 高亮「高考模式」
- [ ] 切换到「标准模式」后，下次评分时工作流使用 4 维度
- [ ] 切换回「高考模式」后，下次评分时工作流使用 7 维度
- [ ] 模式选择刷新页面后保持（localStorage 持久化）
- [ ] 评分中（`running=true`）ModeToggle 不可点击
- [ ] 跑题作文在两种模式下都直接出综合分，不渲染维度卡
- [ ] FinalScoreCard 文案「满分 1.00」不变
- [ ] 所有新单元 / 集成测试通过；`npm run lint` / `npx tsc --noEmit` / `npm test` 全绿
- [ ] `CHANGELOG.md` 与 `README.md` 已同步更新
