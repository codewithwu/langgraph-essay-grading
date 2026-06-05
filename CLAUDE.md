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
