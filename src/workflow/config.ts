export const WEIGHT_RELEVANCE = 0.3;
export const WEIGHT_EVIDENCE = 0.2;
export const WEIGHT_STRUCTURE = 0.2;
export const WEIGHT_EXPRESSION = 0.3;

export const RELEVANCE_THRESHOLD = 0.5;

export const NODE_NAMES = {
  RELEVANCE: "check_relevance",
  EVIDENCE: "check_evidence",
  STRUCTURE: "check_structure",
  EXPRESSION: "check_expression",
  FAN_OUT: "fan_out",
  CALCULATE: "calculate_final_score",
} as const;
