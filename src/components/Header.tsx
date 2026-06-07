import { Link } from "react-router-dom";

type Props = {
  title: string;
  subtitle: string;
  quota?: string;
  quotaExhausted?: boolean;
};

export function Header({ title, subtitle, quota, quotaExhausted = false }: Props) {
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
        {quota && (
          <span className={quotaExhausted ? "app-header-quota exhausted" : "app-header-quota"}>
            {quota}
          </span>
        )}
      </div>
      <div className="app-header-right">
        <a
          className="app-header-qr"
          href="二维码.png"
          target="_blank"
          rel="noreferrer"
          aria-label="扫码加作者"
        >
          <img src="二维码.png" alt="作者二维码" />
          <span className="app-header-qr-tip">扫码可以加作者，支持一下</span>
        </a>
        <a
          className="app-header-repo"
          href="https://github.com/codewithwu/langgraph-essay-grading"
          target="_blank"
          rel="noreferrer"
          aria-label="访问 GitHub 仓库:codewithwu/langgraph-essay-grading"
        >
          <span className="app-header-repo-seal" aria-hidden="true">仓</span>
          <span className="app-header-repo-text">仓库地址</span>
        </a>
        <Link to="/settings" className="icon-btn" aria-label="设置">
          设置
        </Link>
      </div>
    </div>
  );
}
