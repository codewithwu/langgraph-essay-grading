type Props = { score: number; visible: boolean };

export function FinalScoreCard({ score, visible }: Props) {
  return (
    <div className={`final-score-card ${visible ? "active" : ""}`}>
      <div className="final-score-label">综合评分</div>
      <div className="final-score-value">
        <span>{score.toFixed(2)}</span>
        <span className="final-score-unit">/ 1</span>
      </div>
    </div>
  );
}
