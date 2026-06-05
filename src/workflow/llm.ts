import { ChatOpenAI } from "@langchain/openai";
import { loadSettings } from "../lib/settings";

export function getLLM(): ChatOpenAI {
  const { apiKey, baseUrl, modelName } = loadSettings();
  return new ChatOpenAI({
    apiKey,
    configuration: { baseURL: baseUrl },
    model: modelName,
    temperature: 0,
    maxTokens: 2000,
    timeout: 60_000,
  });
}
