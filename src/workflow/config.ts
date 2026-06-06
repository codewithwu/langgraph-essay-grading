export const RELEVANCE_THRESHOLD = 0.5;

export const NODE_NAMES = {
  RELEVANCE: "check_relevance",
  EVIDENCE: "check_evidence",
  STRUCTURE: "check_structure",
  EXPRESSION: "check_expression",
  CONTENT: "check_content",
  DEPTH: "check_depth",
  NOVELTY: "check_novelty",
  FORMATTING: "check_formatting",
  FAN_OUT: "fan_out",
  CALCULATE: "calculate_final_score",
} as const;
