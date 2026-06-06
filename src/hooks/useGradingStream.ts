import { useCallback, useState } from "react";
import { getGraph } from "../workflow/graph";
import type { EssayStateType } from "../workflow/state";
import type { Mode } from "../lib/mode-storage";

export type StreamEvent = {
  node: string;
  update: Record<string, unknown>;
};

type RunInput = Pick<EssayStateType, "topic" | "essay"> & { mode: Mode };

export function useGradingStream() {
  const [events, setEvents] = useState<StreamEvent[]>([]);
  const [done, setDone] = useState(false);
  const [running, setRunning] = useState(false);

  const reset = useCallback(() => {
    setEvents([]);
    setDone(false);
    setRunning(false);
  }, []);

  const run = useCallback(async ({ mode, topic, essay }: RunInput) => {
    reset();
    setRunning(true);
    try {
      const stream = await getGraph(mode).stream(
        { topic, essay, _mode: mode } as unknown as EssayStateType,
        { streamMode: "updates" },
      );
      for await (const event of stream) {
        for (const [node, update] of Object.entries(event)) {
          setEvents((prev) => [...prev, { node, update: update as Record<string, unknown> }]);
        }
      }
    } finally {
      setDone(true);
      setRunning(false);
    }
  }, [reset]);

  return { events, done, running, run, reset };
}
