type Props = { score: number; visible: boolean };

function formatScore(score: number): string {
  return score.toFixed(2);
}

export function FinalScoreCard({ score, visible }: Props) {
  return (
    <div className={`final-score-card ${visible ? "active" : ""}`}>
      <div className="final-score-label">综合评分 / FINAL SCORE</div>
      <div className="final-score-stamp" aria-label={`综合评分 ${formatScore(score)}`}>
        <div>
          <div className="final-score-value">{formatScore(score)}</div>
          <div className="final-score-unit">满分 1.00</div>
        </div>
      </div>
      <div className="final-score-divider">墨韵 · 多智能体评判</div>
    </div>
  );
}
