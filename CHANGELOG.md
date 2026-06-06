# Changelog

## [Unreleased]

### Added
- **高考作文模式** (gaokao mode): 首页 FormSection 顶部新增「标准模式 / 高考模式」切换按钮;开启后,评分工作流从 4 维度升级为 7 维度(审题立意 / 内容论据 / 篇章结构 / 语言文采 / 思想深度 / 创新创意 / 卷面格式),全面对齐 w.md 评分细则中的「基础等级 + 发展等级 + 扣分细则」;总分仍以 1.00 满分,各维度等权 1/7。系统 prompt 拆为 standard / gaokao 两套,gaokao 套内化 60 分制五等评分 + 16 点特征 + 扣分细则。模式选择持久化于 `localStorage: grading-mode-v1`,默认 `gaokao`。
  - 新增模块: `src/lib/mode-storage.ts` (localStorage 读写,含默认值与非法值/抛错兜底)、`src/workflow/dimensions.ts` (维度/权重/标签集中管理,提供 `getDimensions(mode)` / `getWeights(mode)` / `getLabel(node, mode)` 接口)、`src/components/ModeToggle.tsx` (segmented 控件)
  - 编译双 graph: `src/workflow/graph.ts` 中分别编译 `standardGraph` (3 维并行) 与 `gaokaoGraph` (6 维并行),通过 `getGraph(mode)` 选择
  - 状态扩展: `EssayState` 新增 `content / depth / novelty / formatting` 4 个 gaokao 字段 + `_mode` 路由字段
  - 集成测试: `tests/pages/GradingPage.test.tsx` 新增 5 个模式相关用例 (默认/切换/路由/持久化/加载)

### Changed
- **配置**: `src/workflow/config.ts` 中 `NODE_NAMES` 扩展,新增 4 个高考专属节点名;同步移除 `WEIGHT_RELEVANCE` / `WEIGHT_EVIDENCE` / `WEIGHT_STRUCTURE` / `WEIGHT_EXPRESSION` 4 个权重常量（已迁入 `dimensions.ts`）
- **prompt**: `src/workflow/prompts.ts` 中将原 `SYSTEM_PROMPT` 拆为 `STANDARD_SYSTEM_PROMPT` (4 维,沿用旧文) 与 `GAOKAO_SYSTEM_PROMPT` (7 维,内联高考 60 分制评分标准、扣分细则、残篇评定) 两套,新增 `getSystemPrompt(mode)` 选择器
- **API**: `useGradingStream.run` 签名扩展为接受 `mode: Mode` 参数,新增 `reset()` 方法供模式切换时清空旧 events
- 默认评分模式从「标准模式」改为「高考模式」

### Removed
- `src/workflow/config.ts` 中已迁出的 4 个 `WEIGHT_*` 权重常量

### Fixed
- `src/workflow/nodes.ts` 中 `DIM_INSTRUCTIONS` 类型由 `Record<Mode, Record<Dim, string>>` 改为 `Record<Mode, Partial<Record<Dim, string>>>`,允许两种模式拥有不同维度子集;`gradeDim` 中以非空断言 `!` 访问（由图拓扑保证调用合法）
- `tests/workflow/prompts.test.ts` 适配 `SYSTEM_PROMPT` 重命名为 `STANDARD_SYSTEM_PROMPT`
- `tests/hooks/useGradingStream.test.ts` 与 `tests/pages/GradingPage.test.tsx` 的 `vi.mock` 工厂适配新的 `getGraph(mode)` API,`run()` 调用统一传入 `{ mode, topic, essay }`
