import { useCallback, useState } from "react";
import { graph } from "../workflow/graph";
import type { EssayStateType } from "../workflow/state";

export type StreamEvent = {
  node: string;
  update: Record<string, unknown>;
};

export function useGradingStream() {
  const [events, setEvents] = useState<StreamEvent[]>([]);
  const [done, setDone] = useState(false);
  const [running, setRunning] = useState(false);

  const run = useCallback(async (state: Pick<EssayStateType, "topic" | "essay">) => {
    setEvents([]);
    setDone(false);
    setRunning(true);
    try {
      const stream = await graph.stream(state, { streamMode: "updates" });
      for await (const event of stream) {
        for (const [node, update] of Object.entries(event)) {
          setEvents((prev) => [...prev, { node, update: update as Record<string, unknown> }]);
        }
      }
    } finally {
      setDone(true);
      setRunning(false);
    }
  }, []);

  return { events, done, running, run };
}
