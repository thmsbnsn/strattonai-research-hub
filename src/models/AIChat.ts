export type AIHealthStatus = "connected" | "degraded" | "offline";

export interface AIChatCitation {
  kind: string;
  title: string;
  detail: string;
  ticker?: string;
}

export interface AIChatTurn {
  role: "user" | "assistant";
  content: string;
  citations?: AIChatCitation[];
  model?: string;
}

export interface AIChatHealth {
  status: AIHealthStatus;
  assistantLabel: string;
  model: string;
  ollamaReachable: boolean;
  modelAvailable: boolean;
  retrievalMode: string;
  embeddingModelPresent: boolean;
  rerankerModelPresent: boolean;
  semanticRuntimeReady: boolean;
  notes: string[];
}

export interface AIChatResponse {
  answer: string;
  grounded: boolean;
  model: string;
  contextTicker?: string;
  retrievalMode: string;
  citations: AIChatCitation[];
  notes: string[];
}
