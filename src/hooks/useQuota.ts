import { useCallback, useState } from "react";
import { incrementQuota as incrementQuotaStorage, loadQuota, QUOTA_LIMIT as MAX } from "../lib/quota";

export { QUOTA_LIMIT } from "../lib/quota";

type UseQuotaResult = {
  used: number;
  remaining: number;
  exhausted: boolean;
  increment: () => void;
};

export function useQuota(): UseQuotaResult {
  const [used, setUsed] = useState<number>(() => loadQuota().used);

  const increment = useCallback(() => {
    const next = incrementQuotaStorage();
    setUsed(next.used);
  }, []);

  const remaining = Math.max(MAX - used, 0);
  const exhausted = used >= MAX;

  return { used, remaining, exhausted, increment };
}
