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
  relevance: "请评估以下高考作文的「审题立意」维度。考察是否紧扣题目材料、中心是否明确、立意是否深刻、是否有独到见解。重点关注是否切题、是否扣题写作，以及立意的高度与深度。",
  evidence: "请评估以下高考作文的「论据分析」维度。考察材料是否充实、论据是否典型、论证是否有力、事例与观点是否一致。议论文重点看论证方法（举例、对比、比喻、类比等）是否有效；记叙文或散文则看细节、情感是否支撑主旨。",
  structure: "请评估以下高考作文的「篇章结构」维度。考察段落安排、层次推进、过渡衔接、首尾呼应、行文逻辑是否连贯。重点关注是否结构完整、条理清晰、过渡自然。",
  expression: "请评估以下高考作文的「语言表达」维度。考察用词是否贴切、句式是否灵活、修辞是否恰当、是否有文采和意蕴。允许适度的个性化表达，关注整体语言质量而非单点瑕疵。",
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
    (state.evidence?.score ?? 0) * WEIGHT_EVIDENCE +
    (state.structure?.score ?? 0) * WEIGHT_STRUCTURE +
    (state.expression?.score ?? 0) * WEIGHT_EXPRESSION;
  return { final_score: Math.round(final * 100) / 100 };
}
