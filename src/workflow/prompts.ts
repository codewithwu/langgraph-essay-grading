import type { z } from "zod";
import { zodToJsonSchema } from "zod-to-json-schema";

export const SYSTEM_PROMPT = `你是一名经验丰富的高考作文阅卷老师。请遵循以下准则：
1. 严格按照高考作文评分标准进行评判
2. 客观公正，不受作文主题立场影响
3. 评分理由要具体、有依据，引用作文原文
4. 每个维度独立评分，不因某维度表现好而影响其他维度
5. 评分范围 0~1，0.6 为及格线，0.8 以上为优秀`;

export function buildPrompt(schema: z.ZodTypeAny): string {
  const schemaName = schema.description ?? "Output";
  const schemaJson = JSON.stringify(zodToJsonSchema(schema), null, 2);
  return `你是一个 JSON 输出助手。
【输出规则】
1. 只输出纯 JSON 对象，不要包含任何解释、markdown 代码块或其他内容
2. 根据输入内容判断：从用户的输入中提取有效的 ${schemaName} 信息
3. 确保 JSON 字段与 Schema 定义完全一致

【Schema 定义】
## ${schemaName}
${schemaJson}
`;
}
