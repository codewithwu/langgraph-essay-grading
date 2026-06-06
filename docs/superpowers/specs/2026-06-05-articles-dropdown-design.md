# 高考作文评分系统：内置历年高考作文题（articles.md + 下拉选择）

**日期**：2026-06-05
**状态**：待用户审阅
**目标**：把 10 道 2008–2018 年高考作文题整理为 `src/data/articles.md`，在 GradingPage 的「作文题目」输入框上方加一个下拉框，选中后把完整题目（含材料）回填到输入框；输入框仍可自由输入。

---

## 1. 背景与动机

GradingPage 的 FormSection 当前的「作文题目」只有自由文本输入。对评分系统的试用者来说：

- 没有题目就只能随手写一段话，缺少评分参考基准
- 用户自己抄题既慢又容易抄错

把精选的历年高考作文题内置进系统，试用者能 1 选即用，既保留「自由输入」的最大灵活度，又显著降低试用门槛。

**关键约束**：

- 数据必须是 markdown，方便后续手动增删
- 加载方式要兼容现有 GitHub Pages 静态部署（无后端、无 CORS 风险）
- 改动必须局部化：只动 FormSection，不动 GradingPage、不动评分工作流

---

## 2. 架构总览

```
articles.md (?raw, Vite 静态导入)
    │ build-time 内联进 JS 包
    ▼
src/lib/articles.ts → parseArticles(raw) → Article[]
    │
    ▼
FormSection props.articles
    │
    ▼
UI：select + input 双控件
    │ 选中 → setTopic(article.prompt)
    ▼
onSubmit(topic, essay) — GradingPage 接口不变
```

**为什么选 ?raw 而不是 fetch**：

- 构建期内联进 bundle，部署到 GH Pages 无 404 / CORS 风险
- 解析器在模块加载时同步执行，UI 零异步加载态
- 与现有 `import` 规范一致

---

## 3. 数据格式

### 3.1 `src/data/articles.md`

```markdown
# 历年高考作文题（2008-2018）

- 2018年 全国卷I：「世纪宝宝」与中国梦
  阅读材料，结合2000-2018年发生的大事件（如汶川地震、奥运会、天宫一号等），给2035年的18岁青年写一篇文章。
- 2018年 北京卷：新时代新青年 / 绿水青山
  二选一，议论文谈青年与时代的关系，或记叙文谈生态文明。
...
```

- 每条以 `- ` 开头作为标题行
- 紧跟的缩进行（≥2 空格）作为材料说明，可多行
- 空行、顶部 `#` 标题行、其他文本均忽略

### 3.2 `Article` 类型

```ts
export type Article = {
  id: string;      // 稳定 id：年份-序号（如 "2018-1"）
  title: string;   // 标题行去掉 "- " 前缀
  prompt: string;  // 标题行 + 换行 + 材料行（去前导 2 空格），用于回填到 input
};
```

---

## 4. 解析器

**文件**：`src/lib/articles.ts`

**接口**：

```ts
export function parseArticles(raw: string): Article[];
```

**规则**：

1. 按行扫描；遇到以 `- ` 开头的行视为新条目起点
2. 标题 = 该行去掉 `- ` 前缀并 `trim()`
3. 材料 = 紧接的缩进行（≥2 空格或 1 个 tab 开头），去掉前导空白后用 `\n` 拼接
4. id = 从标题行中提取首个 4 位年份（`\d{4}`），与该年份内的出现顺序拼接（如 `2018-1`）；标题中没有 4 位年份则用 `idx-${全局序号}`
5. 空标题条目跳过并 `console.warn`
6. 末尾空行、条目无材料行时 `prompt = title`（不抛错）
7. 输入字符串为非 string（type 异常）时返回 `[]`

**模块加载时**：

```ts
import articlesRaw from "src/data/articles.md?raw";
export const ARTICLES: Article[] = parseArticles(articlesRaw);
```

---

## 5. UI 改动

只改 `src/components/FormSection.tsx`：

```tsx
<form>
  <div className="form-group">
    <label htmlFor="topic">作文题目</label>
    <select
      id="article-select"
      value={selected}
      onChange={(e) => {
        const v = e.target.value;
        setSelected(v);
        const a = ARTICLES.find((x) => x.id === v);
        if (a) setTopic(a.prompt);
      }}
      disabled={disabled}
    >
      <option value="">—— 选择题目 ——</option>
      {ARTICLES.map((a) => (
        <option key={a.id} value={a.id}>{a.title}</option>
      ))}
    </select>
    <input
      type="text"
      id="topic"
      placeholder="请输入或选择作文题目..."
      value={topic}
      onChange={(e) => setTopic(e.target.value)}
      disabled={disabled}
    />
  </div>
  ...
</form>
```

- 选中下拉项 → setTopic(a.prompt)；不重置 selected（保持选中状态）
- 手动编辑 input → 不动 selected（视觉上 select 与 input 解耦）
- `disabled` 透传：评分中两个控件同步禁用
- onSubmit 校验：topic / essay 仍为非空

**GradingPage.tsx 不变**——`onSubmit(topic, essay)` 接口不变。

**样式**：复用 `.form-group`；select 用浏览器默认 + 与 input 同样的 padding/border；不新增 CSS。

---

## 6. 错误处理

| 场景 | 行为 |
|------|------|
| 解析器遇到空标题 | 跳过 + `console.warn`，继续解析 |
| 解析器遇到无材料条目 | 正常返回，prompt = title（单行） |
| articles.md 损坏 / 0 条目 | UI 仍显示，select 只有默认项；不阻塞评分 |
| Vite ?raw 加载失败 | 不可能发生（构建期静态导入） |
| 用户清空 input 后想再用下拉 | 正常下拉选择即可，不需额外操作 |

---

## 7. 测试

**新增**：`tests/lib/articles.test.ts`（镜像 `src/lib/articles.ts`）

用例：

1. 解析 10 道题全部正确（按用户原始内容撰写 fixture）
2. 标题/材料分隔正确：`- ` 识别、材料缩进 2 空格
3. 顺序稳定：返回数组顺序与 markdown 出现顺序一致
4. id 唯一：10 道题无重复 id
5. 容错：空标题跳过、损坏输入不抛错

不新增 FormSection 组件测试（项目无组件测试先例，不引入新依赖）。

---

## 8. 文档与变更记录

- `CHANGELOG.md` 加 `[Unreleased]` 条目：
  - `feat(grading): 内置 10 道历年高考作文题，支持下拉选择回填到题目输入框`
- `README.md` 「使用流程」步骤 5 增加「或从下拉选择题目」一句

---

## 9. 范围外（不做）

- 不做"按年份/卷别筛选"下拉
- 不做"收藏常用题目"功能
- 不改 GradingPage / 工作流 / settings
- 不引入新依赖（Vite ?raw 是内置能力）
- 不写组件测试
