import { HumanMessage, SystemMessage } from "@langchain/core/messages";
import { ScoreDetail, type EssayStateType } from "./state";
import { SYSTEM_PROMPT, buildPrompt } from "./prompts";
import { getLLM } from "./llm";
import {
  WEIGHT_EVIDENCE,
  WEIGHT_EXPRESSION,
  WEIGHT_RELEVANCE,
  WEIGHT_STRUCTURE,
} from "./config";

type Dim = "relevance" | "evidence" | "structure" | "expression";

const DIM_INSTRUCTIONS: Record<Dim, string> = {
  relevance: "请评估以下高考作文的审题立意。考察是否切题、立意是否深刻。",
  evidence: "请评估以下高考作文的论据分析。考察材料是否充实、论据是否有力。",
  structure: "请评估以下高考作文的结构。考察行文逻辑、段落衔接是否合理。",
  expression: "请评估以下高考作文的语言文采。考察用词是否贴切、修辞是否恰当、句式是否灵活。",
};

async function gradeDim(
  state: EssayStateType,
  dim: Dim,
): Promise<Partial<EssayStateType>> {
  const llm = getLLM().withStructuredOutput(ScoreDetail);
  const messages = [
    new SystemMessage(buildPrompt(ScoreDetail) + SYSTEM_PROMPT),
    new HumanMessage(
      `${DIM_INSTRUCTIONS[dim]}\n给出 0 到 1 之间的分数，并说明理由。\n\n题目：${state.topic}\n\n作文：${state.essay}`,
    ),
  ];
  return { [dim]: await llm.invoke(messages) } as Partial<EssayStateType>;
}

export async function check_relevance(
  state: EssayStateType,
): Promise<Partial<EssayStateType>> {
  return gradeDim(state, "relevance");
}

export async function check_evidence(
  state: EssayStateType,
): Promise<Partial<EssayStateType>> {
  return gradeDim(state, "evidence");
}

export async function check_structure(
  state: EssayStateType,
): Promise<Partial<EssayStateType>> {
  return gradeDim(state, "structure");
}

export async function check_expression(
  state: EssayStateType,
): Promise<Partial<EssayStateType>> {
  return gradeDim(state, "expression");
}

export function calculate_final_score(
  state: EssayStateType,
): Partial<EssayStateType> {
  const final =
    state.relevance.score * WEIGHT_RELEVANCE +
    state.evidence.score * WEIGHT_EVIDENCE +
    state.structure.score * WEIGHT_STRUCTURE +
    state.expression.score * WEIGHT_EXPRESSION;
  return { final_score: Math.round(final * 100) / 100 };
}
