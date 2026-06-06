# Changelog

## [Unreleased]

### Changed
- **配置**: 默认 LLM 连接信息（含 API Key）外置到 `src/config/llm-defaults.json`，新用户首次访问无需任何配置即可使用；老用户 localStorage 中的自定义配置仍然优先
- **重构**: 整个项目从 Python (FastAPI + LangGraph) 迁移到 TypeScript (Vite + React)
- **架构**: 从后端 + 前端架构改为纯前端 SPA，LLM API Key 由用户在浏览器内配置
- **部署目标**: 改为 GitHub Pages 静态部署
- **UI**: 重新设计为「墨韵」现代中式编辑美学——宣纸底色 + 墨黑主文 + 朱砂印章强调；引入 Noto Serif SC / Noto Sans SC / Inter / Ma Shan Zheng 字体系统；评分卡加入序号徽章、悬浮抬升、综合分改为盖印式印章（带印泥噪点纹理与微抖动动画）

### Added
- React + TypeScript 前端
- `/settings` 页面管理 LLM 连接信息（API Key / BaseURL / 模型名），存于 localStorage
- GitHub Actions 自动部署到 gh-pages
- Vitest 单元测试覆盖 settings / state / prompts / routes / graph / hook
- 内置 10 道 2008-2018 年高考作文题（`src/data/articles.md`），GradingPage 作文题目输入框上方支持下拉选择并回填
- 体验提升：表单实时字符计数、按钮 hover 朱砂流光与右移箭头、加载态墨滴落入动画、卡片按维度序号 stagger reveal、印章盖下弹跳动效、自定义朱砂滚动条与选区配色
- **额度限制**: 每个浏览器 localStorage 累计只能使用「开始评分」10 次,达到上限后按钮置灰并提示;通过 `src/lib/quota.ts` + `src/hooks/useQuota.ts` 实现,头/表单区持续显示「已用 X/10」
- 集成测试 `tests/pages/GradingPage.test.tsx`: 验证配额耗尽时 `run` 不被调用,锁定 Enter 键短路修复

### Fixed
- **配额绕过**: `GradingPage.handleSubmit` 增加 `if (exhausted) return` 短路,防止 Enter 键在 disabled 按钮之外触发 `run` 调用并绕过配额

### Changed
- 头栏 `.app-header-quota.exhausted` 改用 `--vermillion` / `--vermillion-ink` 令牌,与全局朱砂主题保持一致

### Removed
- 全部 Python 源码（langgraph_essay_grading、langchain_agent、FastAPI 服务层）
- Python Notebook、pyproject.toml、uv.lock、.venv
- .env（API Key 改由前端用户配置）
