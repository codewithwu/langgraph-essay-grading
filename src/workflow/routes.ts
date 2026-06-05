import { RELEVANCE_THRESHOLD } from "./config";
import type { EssayStateType } from "./state";

export function routeRelevance(
  state: EssayStateType,
): "fan_out" | "calculate_final_score" {
  return state.relevance.score > RELEVANCE_THRESHOLD
    ? "fan_out"
    : "calculate_final_score";
}
