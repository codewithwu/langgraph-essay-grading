# 高考作文评分系统 | Gaokao Essay Grading System

基于 LangGraph 的多维度智能评分系统，对高考作文进行审题立意、论据分析、结构评估、语言文采四维度评分。

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

### 流式输出

Web API 支持 SSE 流式返回，实时展示每个维度的评分进度与结果。

## 技术架构

```
用户输入 → FastAPI → EssayState → LangGraph → [条件路由] → [并行LLM调用] → 综合评分
```

- **状态管理**：LangGraph TypedDict 状态机
- **LLM 调用**：LangChain with structured output（Pydantic ScoreDetail）
- **Web 框架**：FastAPI + uvicorn + SSE-Starlette
- **前端**：纯 HTML/CSS/JS，无框架依赖

## 项目结构

```
langgraph_essay_grading/    # 核心 LangGraph 评分工作流
├── state.py                # EssayState 定义
├── graph.py                # 图构建与条件路由
├── nodes.py                # 各评分节点实现
├── config.py               # 维度权重与阈值配置
└── prompts.py              # 系统提示词

langchain_agent/            # 可复用的 Agent 工具库
├── utils/llm_factory.py    # 多提供商 LLM 客户端工厂
└── prompts/base.py         # JSON 输出提示词构建

src/                        # Web 服务层
├── main.py                 # FastAPI 入口
├── routers/grading.py      # 评分 API 路由
├── services/grading.py     # 评分服务封装
└── static/index.html       # 前端页面
```

## 快速开始

```bash
# 安装依赖
source .venv/bin/activate
uv sync

# 启动 Web 服务
uv run python src/main.py

# CLI 演示
uv run python main.py
```

## API 接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/essays/grade` | POST | 同步评分，返回完整结果 |
| `/api/essays/grade/stream` | POST | SSE 流式评分，实时推送各维度结果 |
| `/api/essays/health` | GET | 健康检查 |

## 环境变量

| 变量 | 说明 |
|------|------|
| `LING_API_KEY` | 百灵 API 密钥 |
| `LING_BASEURL` | 百灵 API 地址 |
| `LING_MODEL_NAME` | 模型名称 |

详情参见 `.env.example`。