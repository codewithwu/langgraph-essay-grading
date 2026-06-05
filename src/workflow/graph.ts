import { END, START, StateGraph } from "@langchain/langgraph";
import { EssayState, type EssayStateType } from "./state";
import {
  calculate_final_score,
  check_evidence,
  check_expression,
  check_relevance,
  check_structure,
} from "./nodes";
import { routeRelevance } from "./routes";
import { NODE_NAMES } from "./config";

function fanOut(_: EssayStateType): Record<string, never> {
  return {};
}

const workflow = new StateGraph(EssayState)
  .addNode(NODE_NAMES.RELEVANCE, check_relevance)
  .addNode(NODE_NAMES.FAN_OUT, fanOut)
  .addNode(NODE_NAMES.EVIDENCE, check_evidence)
  .addNode(NODE_NAMES.STRUCTURE, check_structure)
  .addNode(NODE_NAMES.EXPRESSION, check_expression)
  .addNode(NODE_NAMES.CALCULATE, calculate_final_score)
  .addEdge(START, NODE_NAMES.RELEVANCE)
  .addConditionalEdges(NODE_NAMES.RELEVANCE, routeRelevance, {
    fan_out: NODE_NAMES.FAN_OUT,
    calculate_final_score: NODE_NAMES.CALCULATE,
  })
  .addEdge(NODE_NAMES.FAN_OUT, NODE_NAMES.EVIDENCE)
  .addEdge(NODE_NAMES.FAN_OUT, NODE_NAMES.STRUCTURE)
  .addEdge(NODE_NAMES.FAN_OUT, NODE_NAMES.EXPRESSION)
  .addEdge(NODE_NAMES.EVIDENCE, NODE_NAMES.CALCULATE)
  .addEdge(NODE_NAMES.STRUCTURE, NODE_NAMES.CALCULATE)
  .addEdge(NODE_NAMES.EXPRESSION, NODE_NAMES.CALCULATE)
  .addEdge(NODE_NAMES.CALCULATE, END);

export const graph = workflow.compile();
