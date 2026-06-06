import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Header } from "../components/Header";
import { FormSection } from "../components/FormSection";
import { LoadingBar } from "../components/LoadingBar";
import { ScoreCard } from "../components/ScoreCard";
import { SkeletonCard } from "../components/SkeletonCard";
import { FinalScoreCard } from "../components/FinalScoreCard";
import { useGradingStream } from "../hooks/useGradingStream";
import { useQuota } from "../hooks/useQuota";
import { loadSettings } from "../lib/settings";
import type { ScoreDetail } from "../workflow/state";
import { NODE_NAMES } from "../workflow/config";
import { QUOTA_LIMIT } from "../hooks/useQuota";
import { getLabel } from "../workflow/dimensions";
import { loadMode, saveMode, type Mode } from "../lib/mode-storage";

const LOADING_TEXTS: Record<string, string> = {
  [NODE_NAMES.RELEVANCE]: "智能体正在审题...",
  [NODE_NAMES.FAN_OUT]: "审题完成，正在启动多维度并行评分...",
  [NODE_NAMES.EVIDENCE]: "正在分析论据...",
  [NODE_NAMES.STRUCTURE]: "正在评估结构...",
  [NODE_NAMES.EXPRESSION]: "正在鉴赏语言...",
  [NODE_NAMES.CONTENT]: "正在分析内容与论据...",
  [NODE_NAMES.DEPTH]: "正在评估思想深度...",
  [NODE_NAMES.NOVELTY]: "正在评估创新创意...",
  [NODE_NAMES.FORMATTING]: "正在检查卷面格式...",
  [NODE_NAMES.CALCULATE]: "正在计算综合评分...",
};

const GAOKAO_PARALLEL = [
  NODE_NAMES.CONTENT,
  NODE_NAMES.STRUCTURE,
  NODE_NAMES.EXPRESSION,
  NODE_NAMES.DEPTH,
  NODE_NAMES.NOVELTY,
  NODE_NAMES.FORMATTING,
] as const;

const STANDARD_PARALLEL = [
  NODE_NAMES.EVIDENCE,
  NODE_NAMES.STRUCTURE,
  NODE_NAMES.EXPRESSION,
] as const;

function extractScoreDetail(node: string, update: Record<string, unknown>): ScoreDetail | null {
  const key = node.replace("check_", "");
  const detail = (update as Record<string, unknown>)[key] ?? update[node];
  if (
    detail &&
    typeof detail === "object" &&
    "score" in detail &&
    "reason" in detail &&
    typeof (detail as ScoreDetail).score === "number"
  ) {
    return detail as ScoreDetail;
  }
  return null;
}

export function GradingPage() {
  const navigate = useNavigate();
  const { events, done, running, run, reset } = useGradingStream();
  const { used, exhausted, increment } = useQuota();
  const [mode, setMode] = useState<Mode>(() => loadMode());

  useEffect(() => {
    if (!loadSettings().apiKey) navigate("/settings", { replace: true });
  }, [navigate]);

  useEffect(() => {
    saveMode(mode);
    reset();
  }, [mode, reset]);

  const latestLoadingText = useMemo(() => {
    for (let i = events.length - 1; i >= 0; i--) {
      const text = LOADING_TEXTS[events[i].node];
      if (text) return text;
    }
    return LOADING_TEXTS[NODE_NAMES.RELEVANCE];
  }, [events]);

  const relevanceEvent = events.find((e) => e.node === NODE_NAMES.RELEVANCE);
  const finalScoreUpdate = events.find((e) => e.node === NODE_NAMES.CALCULATE)?.update as
    | { final_score?: number }
    | undefined;

  const parallelDims = mode === "gaokao" ? GAOKAO_PARALLEL : STANDARD_PARALLEL;

  function handleModeChange(next: Mode) {
    if (running) return;
    setMode(next);
  }

  function handleSubmit(topic: string, essay: string) {
    if (exhausted) return;
    increment();
    run({ mode, topic, essay }).catch((err) => alert(`评分请求失败: ${err.message ?? err}`));
  }

  const showResults = events.length > 0;

  let dimensionIndex = 0;
  const nextIndex = () => ++dimensionIndex;

  return (
    <div className="container">
      <Header
        title="作文评分智能体"
        subtitle="基于 LangGraph 的多维度智能评分"
        quota={exhausted ? `已达上限(${QUOTA_LIMIT}/${QUOTA_LIMIT})` : `已用 ${used}/${QUOTA_LIMIT}`}
        quotaExhausted={exhausted}
      />

      <FormSection
        disabled={running}
        onSubmit={handleSubmit}
        quotaExhausted={exhausted}
        mode={mode}
        onModeChange={handleModeChange}
      />
      <LoadingBar visible={running} text={done ? "评分完成" : latestLoadingText} />

      <div className={`results-section ${showResults ? "active" : ""}`}>
        {showResults && (
          <h2 className="section-title">
            <span>{mode === "gaokao" ? "高考模式 · 多维度评分" : "多维度评分"}</span>
            <small>{mode === "gaokao" ? "GAOKAO MODE" : "DIMENSIONAL ANALYSIS"}</small>
          </h2>
        )}
        <div className="score-grid">
          {relevanceEvent && (() => {
            const d = extractScoreDetail(NODE_NAMES.RELEVANCE, relevanceEvent.update);
            return d ? (
              <ScoreCard
                title={getLabel(NODE_NAMES.RELEVANCE, mode)}
                detail={d}
                index={nextIndex()}
              />
            ) : null;
          })()}

          {parallelDims.map((dim) => {
            const event = events.find((e) => e.node === dim);
            if (event) {
              const d = extractScoreDetail(dim, event.update);
              if (d) return <ScoreCard key={dim} title={getLabel(dim, mode)} detail={d} index={nextIndex()} />;
            }
            return relevanceEvent ? <SkeletonCard key={dim} /> : null;
          })}

          {finalScoreUpdate?.final_score !== undefined && (
            <FinalScoreCard score={finalScoreUpdate.final_score} visible={done} />
          )}
        </div>
      </div>
    </div>
  );
}
