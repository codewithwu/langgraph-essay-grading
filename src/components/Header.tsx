import { Link } from "react-router-dom";

type Props = { title: string; subtitle: string };

export function Header({ title, subtitle }: Props) {
  return (
    <div className="app-header">
      <div>
        <h1>{title}</h1>
        <p className="subtitle">{subtitle}</p>
      </div>
      <Link to="/settings" className="icon-btn" aria-label="设置">⚙ 设置</Link>
    </div>
  );
}
