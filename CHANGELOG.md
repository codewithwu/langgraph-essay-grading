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
