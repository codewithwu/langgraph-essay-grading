import { END, START, StateGraph } from "@langchain/langgraph";
import { EssayState, type EssayStateType } from "./state";
import {
  calculate_final_score,
  check_content,
  check_depth,
  check_evidence,
  check_expression,
  check_formatting,
  check_novelty,
  check_relevance,
  check_structure,
} from "./nodes";
import { routeRelevance } from "./routes";
import { NODE_NAMES } from "./config";
import type { Mode } from "../lib/mode-storage";

function fanOut(_: EssayStateType): Record<string, never> {
  return {};
}

// 标准模式: 4 维(evidence / structure / expression 并行)
export const standardGraph = new StateGraph(EssayState)
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
  .addEdge(NODE_NAMES.CALCULATE, END)
  .compile();

// 高考模式: 6 维(content / structure / expression / depth / novelty / formatting 并行)
export const gaokaoGraph = new StateGraph(EssayState)
  .addNode(NODE_NAMES.RELEVANCE, check_relevance)
  .addNode(NODE_NAMES.FAN_OUT, fanOut)
  .addNode(NODE_NAMES.CONTENT, check_content)
  .addNode(NODE_NAMES.STRUCTURE, check_structure)
  .addNode(NODE_NAMES.EXPRESSION, check_expression)
  .addNode(NODE_NAMES.DEPTH, check_depth)
  .addNode(NODE_NAMES.NOVELTY, check_novelty)
  .addNode(NODE_NAMES.FORMATTING, check_formatting)
  .addNode(NODE_NAMES.CALCULATE, calculate_final_score)
  .addEdge(START, NODE_NAMES.RELEVANCE)
  .addConditionalEdges(NODE_NAMES.RELEVANCE, routeRelevance, {
    fan_out: NODE_NAMES.FAN_OUT,
    calculate_final_score: NODE_NAMES.CALCULATE,
  })
  .addEdge(NODE_NAMES.FAN_OUT, NODE_NAMES.CONTENT)
  .addEdge(NODE_NAMES.FAN_OUT, NODE_NAMES.STRUCTURE)
  .addEdge(NODE_NAMES.FAN_OUT, NODE_NAMES.EXPRESSION)
  .addEdge(NODE_NAMES.FAN_OUT, NODE_NAMES.DEPTH)
  .addEdge(NODE_NAMES.FAN_OUT, NODE_NAMES.NOVELTY)
  .addEdge(NODE_NAMES.FAN_OUT, NODE_NAMES.FORMATTING)
  .addEdge(NODE_NAMES.CONTENT, NODE_NAMES.CALCULATE)
  .addEdge(NODE_NAMES.STRUCTURE, NODE_NAMES.CALCULATE)
  .addEdge(NODE_NAMES.EXPRESSION, NODE_NAMES.CALCULATE)
  .addEdge(NODE_NAMES.DEPTH, NODE_NAMES.CALCULATE)
  .addEdge(NODE_NAMES.NOVELTY, NODE_NAMES.CALCULATE)
  .addEdge(NODE_NAMES.FORMATTING, NODE_NAMES.CALCULATE)
  .addEdge(NODE_NAMES.CALCULATE, END)
  .compile();

export function getGraph(mode: Mode) {
  return mode === "gaokao" ? gaokaoGraph : standardGraph;
}

// 向后兼容: 旧代码用 `graph` 导入时默认给 standard
export const graph = standardGraph;
