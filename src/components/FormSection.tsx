import { useState, type FormEvent } from "react";
import { ARTICLES } from "../lib/articles";

type Props = {
  disabled: boolean;
  onSubmit: (topic: string, essay: string) => void;
  quotaExhausted?: boolean;
};

export function FormSection({ disabled, onSubmit, quotaExhausted = false }: Props) {
  const [topic, setTopic] = useState("");
  const [essay, setEssay] = useState("");
  const [selectedArticleId, setSelectedArticleId] = useState("");

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    const t = topic.trim();
    const es = essay.trim();
    if (!t || !es) {
      alert("请填写作文题目和内容");
      return;
    }
    onSubmit(t, es);
  }

  function handleArticleChange(id: string) {
    setSelectedArticleId(id);
    if (!id) return;
    const a = ARTICLES.find((x) => x.id === id);
    if (a) setTopic(a.prompt);
  }

  return (
    <form className="form-section" onSubmit={handleSubmit}>
      <div className="form-group">
        <label htmlFor="topic">作文题目</label>
        <select
          id="article-select"
          className="article-select"
          value={selectedArticleId}
          onChange={(e) => handleArticleChange(e.target.value)}
          disabled={disabled}
        >
          <option value="">—— 选择题目 ——</option>
          {ARTICLES.map((a) => (
            <option key={a.id} value={a.id}>
              {a.title}
            </option>
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
      <div className="form-group">
        <label htmlFor="essay">作文内容</label>
        <textarea
          id="essay"
          placeholder="请输入作文内容..."
          value={essay}
          onChange={(e) => setEssay(e.target.value)}
          disabled={disabled}
        />
        <span className="char-counter" aria-live="polite">
          <strong>{essay.length}</strong> 字
        </span>
      </div>
      <button
        type="submit"
        className="btn-submit"
        disabled={disabled || quotaExhausted}
        title={quotaExhausted ? "免费次数已用完,清空浏览器数据可重置" : undefined}
      >
        {quotaExhausted ? "次数已用完" : disabled ? "评分中" : "开始评分"}
      </button>
    </form>
  );
}
