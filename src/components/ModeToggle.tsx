import type { Mode } from "../lib/mode-storage";

type Props = {
  mode: Mode;
  onChange: (mode: Mode) => void;
  disabled?: boolean;
};

const OPTIONS: { value: Mode; label: string; hint: string }[] = [
  { value: "standard", label: "标准模式", hint: "4 维度" },
  { value: "gaokao", label: "高考模式", hint: "7 维度" },
];

export function ModeToggle({ mode, onChange, disabled = false }: Props) {
  return (
    <div
      className="mode-toggle"
      role="radiogroup"
      aria-label="评分模式"
    >
      <span className="mode-toggle-label">评分模式</span>
      <div className="mode-toggle-pills">
        {OPTIONS.map((opt) => {
          const active = mode === opt.value;
          return (
            <button
              key={opt.value}
              type="button"
              role="radio"
              aria-checked={active}
              className={`mode-toggle-pill ${active ? "active" : ""}`}
              disabled={disabled}
              onClick={() => onChange(opt.value)}
            >
              <span className="mode-toggle-pill-label">{opt.label}</span>
              <span className="mode-toggle-pill-hint">{opt.hint}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
