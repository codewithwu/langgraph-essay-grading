import type { ScoreDetail } from "../workflow/state";

type Props = {
  title: string;
  detail: ScoreDetail;
  index: number;
};

function scoreClass(score: number): string {
  if (score >= 0.8) return "score-high";
  if (score >= 0.6) return "score-mid";
  return "score-low";
}

function formatScore(score: number): string {
  return score.toFixed(2);
}

export function ScoreCard({ title, detail, index }: Props) {
  return (
    <div className="score-card">
      <div className="score-card-header">
        <span className="score-card-title" data-index={`0${index}`}>
          {title}
        </span>
        <span className={`score-badge ${scoreClass(detail.score)}`}>
          {formatScore(detail.score)}
        </span>
      </div>
      <p className="score-reason">{detail.reason}</p>
    </div>
  );
}
