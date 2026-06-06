import { useEffect, useMemo } from "react";
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

const NODE_LABELS: Record<string, string> = {
  [NODE_NAMES.RELEVANCE]: "审题立意",
  [NODE_NAMES.EVIDENCE]: "论据分析",
  [NODE_NAMES.STRUCTURE]: "结构评估",
  [NODE_NAMES.EXPRESSION]: "语言文采",
};

const LOADING_TEXTS: Record<string, string> = {
  [NODE_NAMES.RELEVANCE]: "智能体正在审题...",
  [NODE_NAMES.FAN_OUT]: "审题完成，正在启动多维度并行评分...",
  [NODE_NAMES.EVIDENCE]: "正在分析论据...",
  [NODE_NAMES.STRUCTURE]: "正在评估结构...",
  [NODE_NAMES.EXPRESSION]: "正在鉴赏语言...",
  [NODE_NAMES.CALCULATE]: "正在计算综合评分...",
};

const PARALLEL_DIMS = [NODE_NAMES.EVIDENCE, NODE_NAMES.STRUCTURE, NODE_NAMES.EXPRESSION] as const;

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
  const { events, done, running, run } = useGradingStream();
  const { used, exhausted, increment } = useQuota();

  useEffect(() => {
    if (!loadSettings().apiKey) navigate("/settings", { replace: true });
  }, [navigate]);

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

  function handleSubmit(topic: string, essay: string) {
    increment();
    run({ topic, essay }).catch((err) => alert(`评分请求失败: ${err.message ?? err}`));
  }

  const showResults = events.length > 0;

  let dimensionIndex = 0;
  const nextIndex = () => ++dimensionIndex;

  return (
    <div className="container">
      <Header
        title="高考作文评分系统"
        subtitle="基于 LangGraph 的多维度智能评分"
        quota={exhausted ? `已达上限(${QUOTA_LIMIT}/${QUOTA_LIMIT})` : `已用 ${used}/${QUOTA_LIMIT}`}
        quotaExhausted={exhausted}
      />

      <FormSection disabled={running} onSubmit={handleSubmit} quotaExhausted={exhausted} />
      <LoadingBar visible={running} text={done ? "评分完成" : latestLoadingText} />

      <div className={`results-section ${showResults ? "active" : ""}`}>
        {showResults && (
          <h2 className="section-title">
            <span>多维度评分</span>
            <small>DIMENSIONAL ANALYSIS</small>
          </h2>
        )}
        <div className="score-grid">
          {relevanceEvent && (() => {
            const d = extractScoreDetail(NODE_NAMES.RELEVANCE, relevanceEvent.update);
            return d ? <ScoreCard title={NODE_LABELS[NODE_NAMES.RELEVANCE]} detail={d} index={nextIndex()} /> : null;
          })()}

          {PARALLEL_DIMS.map((dim) => {
            const event = events.find((e) => e.node === dim);
            if (event) {
              const d = extractScoreDetail(dim, event.update);
              if (d) return <ScoreCard key={dim} title={NODE_LABELS[dim]} detail={d} index={nextIndex()} />;
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
