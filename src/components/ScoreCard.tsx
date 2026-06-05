import type { ScoreDetail } from "../workflow/state";

type Props = {
  title: string;
  detail: ScoreDetail;
};

function scoreClass(score: number): string {
  if (score >= 0.8) return "score-high";
  if (score >= 0.6) return "score-mid";
  return "score-low";
}

export function ScoreCard({ title, detail }: Props) {
  return (
    <div className="score-card">
      <div className="score-card-header">
        <span className="score-card-title">{title}</span>
        <span className={`score-badge ${scoreClass(detail.score)}`}>
          {detail.score.toFixed(2)}
        </span>
      </div>
      <p className="score-reason">{detail.reason}</p>
    </div>
  );
}
