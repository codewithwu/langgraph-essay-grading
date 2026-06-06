const STORAGE_KEY = "grading-quota-v1";
const MAX_USES = 10;

export type QuotaState = { used: number };

export const QUOTA_LIMIT = MAX_USES;

function clampUsed(raw: unknown): number {
  if (typeof raw !== "number" || Number.isNaN(raw)) return 0;
  const floored = Math.floor(raw);
  if (floored < 0) return 0;
  if (floored > MAX_USES) return MAX_USES;
  return floored;
}

export function loadQuota(): QuotaState {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return { used: 0 };
    const parsed = JSON.parse(raw) as { used?: unknown };
    return { used: clampUsed(parsed.used) };
  } catch {
    return { used: 0 };
  }
}

export function saveQuota(state: QuotaState): void {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
}

export function incrementQuota(): QuotaState {
  const current = loadQuota();
  const next: QuotaState = { used: Math.min(current.used + 1, MAX_USES) };
  try {
    saveQuota(next);
  } catch (err) {
    console.warn("quota: failed to persist", err);
    return current;
  }
  return next;
}
