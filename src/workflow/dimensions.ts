import type { Mode } from "../lib/mode-storage";

export type Dim = {
  /** LangGraph 节点名 */
  node: string;
  /** EssayState 中的字段名(节点输出会写入该字段) */
  field: string;
  /** 中文标签,用于 UI 卡片标题 */
  label: string;
  /** 0-1 之间的权重;所有 dim 权重和必须 = 1 */
  weight: number;
};

export const STANDARD_DIMS: readonly Dim[] = [
  { node: "check_relevance", field: "relevance", label: "审题立意", weight: 0.3 },
  { node: "check_evidence", field: "evidence", label: "论据分析", weight: 0.2 },
  { node: "check_structure", field: "structure", label: "结构评估", weight: 0.2 },
  { node: "check_expression", field: "expression", label: "语言文采", weight: 0.3 },
];

export const GAOKAO_DIMS: readonly Dim[] = [
  { node: "check_relevance", field: "relevance", label: "审题立意", weight: 1 / 7 },
  { node: "check_content", field: "content", label: "内容论据", weight: 1 / 7 },
  { node: "check_structure", field: "structure", label: "篇章结构", weight: 1 / 7 },
  { node: "check_expression", field: "expression", label: "语言文采", weight: 1 / 7 },
  { node: "check_depth", field: "depth", label: "思想深度", weight: 1 / 7 },
  { node: "check_novelty", field: "novelty", label: "创新创意", weight: 1 / 7 },
  { node: "check_formatting", field: "formatting", label: "卷面格式", weight: 1 / 7 },
];

export function getDimensions(mode: Mode): readonly Dim[] {
  return mode === "gaokao" ? GAOKAO_DIMS : STANDARD_DIMS;
}

export function getWeights(mode: Mode): Map<string, number> {
  const dims = getDimensions(mode);
  const m = new Map<string, number>();
  for (const d of dims) m.set(d.field, d.weight);
  return m;
}

export function getLabel(node: string): string {
  const all = [...STANDARD_DIMS, ...GAOKAO_DIMS];
  return all.find((d) => d.node === node)?.label ?? node;
}
