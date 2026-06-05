type Props = { visible: boolean; text: string };

export function LoadingBar({ visible, text }: Props) {
  return (
    <div className={`loading-bar ${visible ? "active" : ""}`}>
      <div className="loading-dots">
        <span /><span /><span />
      </div>
      <div className="loading-text">{text}</div>
    </div>
  );
}
