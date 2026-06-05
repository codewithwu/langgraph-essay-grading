# LLM 默认配置外置到 JSON 文件

**日期**：2026-06-06
**状态**：已批准

## 目标

新用户首次访问页面，**无需手动填写任何配置**即可连接到百灵的 `Ling-2.6-1T` 模型并开始评分。
将 `apiKey`、`baseUrl`、`modelName` 三项默认值集中外置到 `src/config/llm-defaults.json`，
取代当前 `src/lib/settings.ts` 中的内联硬编码。

## 背景与权衡

当前 `src/lib/settings.ts` 的 `DEFAULT_SETTINGS` 已经预填了 `baseUrl` 和 `modelName`，
但 `apiKey` 是空字符串，因此新用户必须先进设置页填入 Key 才能使用。

项目所有者在了解以下事实后，决定接受公开 Key 的风险：

- 项目是纯前端 SPA，部署到 GitHub Pages 是公开仓库
- Key 会同时进入 git 历史和打包后的 JS bundle，任何访客可在 DevTools 中提取
- 任何"前端混淆 / base64 / 拆分"都是安全剧场，不构成实质保护
- 真正能保护 Key 的方案（后端代理）需要额外架构，超出本次范围

**风险缓解（项目所有者承诺在 provider 端配套执行）**：

- 对该 Key 设置月度额度上限（例如 ¥5 / 月），把被盗刷的潜在损失封顶
- 一旦发现异常用量，立即在 provider 后台 revoke 并替换 JSON 中的 Key

## 文件改动

### 1. 新增 `src/config/llm-defaults.json`

```json
{
  "apiKey": "sk-studio-2722acfd3da941e4b2f1326802c5d7d3",
  "baseUrl": "https://api.tbox.cn/api/llm/v1/",
  "modelName": "Ling-2.6-1T"
}
```

JSON 三个字段必须与 `Settings` 类型完全对齐（key 名、类型）。
TypeScript 在导入时会做结构检查。

### 2. 修改 `src/lib/settings.ts`

**改动前**：
```typescript
export const DEFAULT_SETTINGS: Settings = {
  apiKey: "",
  baseUrl: "https://api.tbox.cn/api/llm/v1/",
  modelName: "Ling-2.6-1T",
};
```

**改动后**：
```typescript
import defaults from "../config/llm-defaults.json";

export const DEFAULT_SETTINGS: Settings = defaults;
```

`Settings` 类型定义保持不变；`loadSettings()` 和 `saveSettings()` 实现不变。
`tsconfig.json` 已开启 `resolveJsonModule`，不需要改。

## 行为

| 场景 | 行为 |
|---|---|
| 首次访问（localStorage 为空） | `loadSettings()` 返回 `DEFAULT_SETTINGS`，含完整 API Key，`getLLM()` 直接可用 |
| 老用户（localStorage 已存自定义配置） | 现有合并逻辑 `{ ...DEFAULT_SETTINGS, ...JSON.parse(raw) }` 保证用户保存的值优先 |
| 用户主动清空 API Key 并保存 | 保存的空字符串覆盖默认值（用户可显式 opt-out 默认 Key） |
| 设置页「恢复默认」按钮 | 重新填入新的默认值（包含 API Key），与「打开即用」意图一致 |

下游消费者（`getLLM()` / `SettingsPage` / `useGradingStream`）**全部无需改动**，
因为它们都通过 `loadSettings()` 间接访问默认值。

## 测试

### 现有测试自动覆盖
`tests/workflow/settings.test.ts` 已包含 `"returns defaults when storage is empty"`，
会自动比较 `loadSettings()` 与 `DEFAULT_SETTINGS`，
若 JSON 导入失败或字段缺失，该测试会失败。

### 新增测试
在 `tests/workflow/settings.test.ts` 中增加一条：

```typescript
it("default settings is loaded from JSON with all fields populated", () => {
  expect(DEFAULT_SETTINGS.apiKey).toMatch(/^sk-/);
  expect(DEFAULT_SETTINGS.baseUrl).toBe("https://api.tbox.cn/api/llm/v1/");
  expect(DEFAULT_SETTINGS.modelName).toBe("Ling-2.6-1T");
});
```

目的：防止 JSON 文件被意外删除、路径写错、或字段被改名时静默通过类型检查。

## 文档更新

### `CHANGELOG.md`
`[Unreleased]` 的 `Changed` 区域新增一条：

> **预填百灵默认 API Key 到 `src/config/llm-defaults.json`，新用户无需配置即可使用；老用户 localStorage 中的自定义配置仍然优先**

### `README.md`
- 「使用流程」第 2 步改为：
  > 2. （可选）若需替换 provider，进入设置页修改 API Key / BaseURL / 模型名
- 「安全提示」新增一条警告：
  > ⚠️ 当前仓库已预填演示用的百灵 API Key 到 `src/config/llm-defaults.json`，会随 GH Pages bundle 公开；若你 fork 本项目用于生产，请务必先把 JSON 替换成自己的私有 Key，并在 provider 后台设置月度额度上限

## 范围以外

- ❌ 不引入 `.env` 或 Vite 环境变量（已选择硬编码方案）
- ❌ 不改 `.gitignore`（JSON 要被 git 跟踪）
- ❌ 不动 `getLLM()` / `SettingsPage` / `useGradingStream`
- ❌ 不改 `tsconfig.json`（`resolveJsonModule` 已开启）
- ❌ 不引入后端代理（已评估并由项目所有者明确放弃）

## 验证清单

- [ ] `src/config/llm-defaults.json` 存在且三字段齐全
- [ ] `npx tsc --noEmit` 通过
- [ ] `npm run lint` 通过
- [ ] `npm test` 通过（含新增的非空 apiKey 断言）
- [ ] 清空浏览器 localStorage 后访问设置页，三字段全部预填、可直接「测试连接」成功
- [ ] `CHANGELOG.md` 与 `README.md` 已更新
