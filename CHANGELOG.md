# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/).

## [Unreleased]

### Added

- FastAPI 后端接口，支持同步评分 (`POST /api/essays/grade`) 和 SSE 流式评分 (`POST /api/essays/grade/stream`)
- 健康检查接口 (`GET /api/health`)
- SSE 事件格式化工具 (`src/utils/sse.py`)
- 评分服务层，桥接 LangGraph 图流到 async 接口 (`src/services/grading.py`)
- 前端页面 (`static/index.html`)，支持 SSE 流式展示评分过程、loading 动效和骨架屏
