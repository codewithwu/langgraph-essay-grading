const STORAGE_KEY = "grading-mode-v1";
const VALID_MODES = ["standard", "gaokao"] as const;
export type Mode = (typeof VALID_MODES)[number];
export const DEFAULT_MODE: Mode = "gaokao";

function isValidMode(v: unknown): v is Mode {
  return typeof v === "string" && (VALID_MODES as readonly string[]).includes(v);
}

export function loadMode(): Mode {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw === null) return DEFAULT_MODE;
    const parsed: unknown = JSON.parse(raw);
    if (!isValidMode(parsed)) {
      console.warn(`[mode-storage] 非法 mode 值 "${String(parsed)}" 已回退为 ${DEFAULT_MODE}`);
      return DEFAULT_MODE;
    }
    return parsed;
  } catch (err) {
    console.warn(`[mode-storage] 读取失败,回退默认:`, err);
    return DEFAULT_MODE;
  }
}

export function saveMode(mode: Mode): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(mode));
  } catch (err) {
    console.warn(`[mode-storage] 写入失败(忽略):`, err);
  }
}
