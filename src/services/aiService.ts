import type { AIChatHealth, AIChatResponse, AIChatTurn } from "@/models";

const DEFAULT_AI_GATEWAY_URL = (import.meta.env.VITE_AI_GATEWAY_URL || "http://127.0.0.1:8787").replace(/\/$/, "");

type ChatRequest = {
  message: string;
  ticker?: string | null;
  tradingMode?: "paper" | "live";
  conversation?: AIChatTurn[];
};

function offlineHealth(detail: string): AIChatHealth {
  return {
    status: "offline",
    assistantLabel: "Local AI Gateway Offline",
    model: "offline",
    ollamaReachable: false,
    modelAvailable: false,
    retrievalMode: "structured",
    embeddingModelPresent: false,
    rerankerModelPresent: false,
    semanticRuntimeReady: false,
    notes: [detail],
  };
}

export async function getAIHealth() {
  try {
    const response = await fetch(`${DEFAULT_AI_GATEWAY_URL}/health`);
    if (!response.ok) {
      return offlineHealth(`Gateway health check failed with status ${response.status}.`);
    }

    return (await response.json()) as AIChatHealth;
  } catch (error) {
    return offlineHealth(
      error instanceof Error
        ? `Gateway unavailable: ${error.message}`
        : "Gateway unavailable."
    );
  }
}

export async function sendAIChatMessage(request: ChatRequest): Promise<AIChatResponse> {
  try {
    const response = await fetch(`${DEFAULT_AI_GATEWAY_URL}/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        message: request.message,
        ticker: request.ticker,
        tradingMode: request.tradingMode || "paper",
        conversation: request.conversation?.slice(-6).map((turn) => ({
          role: turn.role,
          content: turn.content,
        })) || [],
      }),
    });

    if (!response.ok) {
      throw new Error(`Gateway chat failed with status ${response.status}.`);
    }

    return (await response.json()) as AIChatResponse;
  } catch (error) {
    return {
      answer:
        "The local AI gateway is currently unavailable. Start the local gateway to enable grounded chat over StrattonAI research data.",
      grounded: false,
      model: "offline",
      contextTicker: request.ticker || undefined,
      retrievalMode: "structured",
      citations: [],
      notes: [
        error instanceof Error ? error.message : "Gateway unavailable.",
      ],
    };
  }
}
