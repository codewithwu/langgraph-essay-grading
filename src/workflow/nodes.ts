import { HumanMessage, SystemMessage } from "@langchain/core/messages";
import { ScoreDetail, type EssayStateType } from "./state";
import { buildPrompt, getSystemPrompt } from "./prompts";
import { getLLM } from "./llm";
import type { Mode } from "../lib/mode-storage";

type Dim =
  | "relevance"
  | "evidence"
  | "structure"
  | "expression"
  | "content"
  | "depth"
  | "novelty"
  | "formatting";

const DIM_INSTRUCTIONS: Record<Mode, Record<Dim, string>> = {
  standard: {
    relevance: "请评估以下高考作文的「审题立意」维度。考察是否紧扣题目材料、中心是否明确、立意是否深刻、是否有独到见解。重点关注是否切题、是否扣题写作，以及立意的高度与深度。",
    evidence: "请评估以下高考作文的「论据分析」维度。考察材料是否充实、论据是否典型、论证是否有力、事例与观点是否一致。议论文重点看论证方法（举例、对比、比喻、类比等）是否有效；记叙文或散文则看细节、情感是否支撑主旨。",
    structure: "请评估以下高考作文的「篇章结构」维度。考察段落安排、层次推进、过渡衔接、首尾呼应、行文逻辑是否连贯。重点关注是否结构完整、条理清晰、过渡自然。",
    expression: "请评估以下高考作文的「语言表达」维度。考察用词是否贴切、句式是否灵活、修辞是否恰当、是否有文采和意蕴。允许适度的个性化表达，关注整体语言质量而非单点瑕疵。",
  },
  gaokao: {
    relevance: "请评估「审题立意」维度(对应 w.md 基础等级「内容」项的题意/中心/思想/感情):是否切题、中心是否突出、是否符合题意所涉及的范围/情境/任务要求;立意是否准确、集中、鲜明,有无独到见解。",
    content: "请评估「内容论据」维度(对应 w.md 基础等级「内容」项的材料/论据):内容是否充实、论据是否典型/充足、事例与观点是否一致;议论文看论证方法(举例、对比、比喻、类比等)是否有效;记叙文或散文看细节、情感是否支撑主旨。",
    structure: "请评估「篇章结构」维度(对应 w.md 基础等级「表达」项的结构):段落安排、层次推进、过渡衔接、首尾呼应、行文逻辑是否连贯;是否结构严谨、条理清晰、过渡自然。",
    expression: "请评估「语言文采」维度(对应 w.md 基础等级「表达」项的语言 + 发展等级「有文采」):用词是否贴切、句式是否灵活、修辞是否得当、文句有无表现力;关注整体语言质量与文采,允许适度个性化表达。",
    depth: "请评估「思想深度」维度(对应 w.md 发展等级「深刻」):①是否透过现象看本质 ②是否揭示事物内在的因果关系 ③观点是否具有启发作用。三点居其一即可得高分。",
    novelty: "请评估「创新创意」维度(对应 w.md 发展等级「有创意」):①见解是否新颖 ②材料是否新鲜 ③构思是否精巧 ④推理想象有无独到之处 ⑤是否有个性特征。",
    formatting: "请评估「卷面格式」维度(对应 w.md 扣分细则):错别字数量(1 字扣 1 分,重复不计,封顶 5 分)、标点错误(3 处以上酌情扣分)、字数是否达标(每少 50 字扣 1 分)、是否有标题(无标题扣 2 分)。综合上述给出 0-1 分数(1.00 = 无任何扣分项)。",
  },
};

async function gradeDim(
  state: EssayStateType,
  mode: Mode,
  dim: Dim,
): Promise<Partial<EssayStateType>> {
  const llm = getLLM().withStructuredOutput(ScoreDetail);
  const messages = [
    new SystemMessage(buildPrompt(ScoreDetail) + getSystemPrompt(mode)),
    new HumanMessage(
      `${DIM_INSTRUCTIONS[mode][dim]}\n给出 0 到 1 之间的分数，并说明理由。\n\n题目：${state.topic}\n\n作文：${state.essay}`,
    ),
  ];
  return { [dim]: await llm.invoke(messages) } as Partial<EssayStateType>;
}

export async function check_relevance(
  state: EssayStateType,
): Promise<Partial<EssayStateType>> {
  const mode = state._mode ?? "standard";
  return gradeDim(state, mode, "relevance");
}

export async function check_evidence(
  state: EssayStateType,
): Promise<Partial<EssayStateType>> {
  return gradeDim(state, "standard", "evidence");
}

export async function check_structure(
  state: EssayStateType,
): Promise<Partial<EssayStateType>> {
  const mode = state._mode ?? "standard";
  return gradeDim(state, mode, "structure");
}

export async function check_expression(
  state: EssayStateType,
): Promise<Partial<EssayStateType>> {
  const mode = state._mode ?? "standard";
  return gradeDim(state, mode, "expression");
}

export async function check_content(
  state: EssayStateType,
): Promise<Partial<EssayStateType>> {
  return gradeDim(state, "gaokao", "content");
}

export async function check_depth(
  state: EssayStateType,
): Promise<Partial<EssayStateType>> {
  return gradeDim(state, "gaokao", "depth");
}

export async function check_novelty(
  state: EssayStateType,
): Promise<Partial<EssayStateType>> {
  return gradeDim(state, "gaokao", "novelty");
}

export async function check_formatting(
  state: EssayStateType,
): Promise<Partial<EssayStateType>> {
  return gradeDim(state, "gaokao", "formatting");
}

export function calculate_final_score(
  state: EssayStateType,
): Partial<EssayStateType> {
  const mode = state._mode ?? "standard";
  const weights = mode === "gaokao"
    ? {
        relevance: 1 / 7,
        content: 1 / 7,
        structure: 1 / 7,
        expression: 1 / 7,
        depth: 1 / 7,
        novelty: 1 / 7,
        formatting: 1 / 7,
      }
    : {
        relevance: 0.3,
        evidence: 0.2,
        structure: 0.2,
        expression: 0.3,
      };

  const final = (Object.entries(weights) as [keyof typeof weights, number][])
    .reduce((sum, [field, w]) => {
      const detail = state[field];
      return sum + (detail?.score ?? 0) * w;
    }, 0);

  return { final_score: Math.round(final * 100) / 100 };
}
