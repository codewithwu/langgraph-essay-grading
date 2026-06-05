import { z } from "zod";
import { Annotation } from "@langchain/langgraph";

export const ScoreDetail = z.object({
  score: z.number().min(0).max(1),
  reason: z.string(),
});

export type ScoreDetail = z.infer<typeof ScoreDetail>;

export const EssayState = Annotation.Root({
  topic: Annotation<string>(),
  essay: Annotation<string>(),
  relevance: Annotation<ScoreDetail>(),
  evidence: Annotation<ScoreDetail>(),
  structure: Annotation<ScoreDetail>(),
  expression: Annotation<ScoreDetail>(),
  final_score: Annotation<number>(),
});

export type EssayStateType = typeof EssayState.State;
