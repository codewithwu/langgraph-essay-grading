import { Link } from "react-router-dom";

type Props = { title: string; subtitle: string };

export function Header({ title, subtitle }: Props) {
  return (
    <div className="app-header">
      <div className="app-header-text">
        <div className="app-header-meta">
          <span className="app-header-meta-year">贰零贰陆</span>
          <span>ESSAY GRADING SYSTEM</span>
        </div>
        <h1>
          <span className="wordmark-seal" aria-hidden="true">墨</span>
          {title}
        </h1>
        <p className="subtitle">
          {subtitle}
        </p>
      </div>
      <Link to="/settings" className="icon-btn" aria-label="设置">
        设置
      </Link>
    </div>
  );
}
