const STORAGE_KEY = "grading-settings-v1";

export type Settings = {
  apiKey: string;
  baseUrl: string;
  modelName: string;
};

export const DEFAULT_SETTINGS: Settings = {
  apiKey: "",
  baseUrl: "https://api.tbox.cn/api/llm/v1/",
  modelName: "Ling-2.6-1T",
};

export function loadSettings(): Settings {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return DEFAULT_SETTINGS;
    return { ...DEFAULT_SETTINGS, ...JSON.parse(raw) };
  } catch {
    return DEFAULT_SETTINGS;
  }
}

export function saveSettings(s: Settings): void {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(s));
}
