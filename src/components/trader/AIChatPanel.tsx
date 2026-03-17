import { useEffect, useMemo, useRef, useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { AlertTriangle, Bot, ExternalLink, Loader2, Send, Sparkles, User } from "lucide-react";
import type { AIChatCitation, AIChatTurn } from "@/models";
import { getAIHealth, sendAIChatMessage } from "@/services/aiService";
import type { TradingMode } from "@/hooks/useTradingMode";

type ChatPanelMessage = AIChatTurn & {
  id: string;
};

function getSuggestedPrompts(ticker?: string | null) {
  if (!ticker) {
    return [
      "Summarize the bullish case for NVDA",
      "Show key risks for AAPL",
      "What research supports a TSLA paper trade?",
      "Compare AMD vs NVDA over the next 10D horizon",
    ];
  }

  return [
    `Summarize the current thesis for ${ticker}`,
    `Show the major risks for ${ticker}`,
    `What research supports a paper trade in ${ticker}?`,
    `Compare ${ticker} against its closest peers`,
  ];
}

function healthTone(status: "connected" | "degraded" | "offline") {
  if (status === "connected") {
    return "bg-emerald-500/10 text-emerald-300 border-emerald-500/20";
  }

  if (status === "degraded") {
    return "bg-amber-500/10 text-amber-300 border-amber-500/20";
  }

  return "bg-muted/50 text-muted-foreground border-border";
}

function citationLabel(citation: AIChatCitation) {
  return citation.ticker ? `${citation.title} · ${citation.ticker}` : citation.title;
}

function citationTarget(citation: AIChatCitation) {
  const ticker = citation.ticker?.trim().toUpperCase();
  if (citation.kind === "event") {
    return ticker ? `/events?ticker=${encodeURIComponent(ticker)}` : "/events";
  }
  if (citation.kind === "study" || citation.kind === "signal") {
    return ticker ? `/studies?ticker=${encodeURIComponent(ticker)}` : "/studies";
  }
  if (citation.kind === "profile" || citation.kind === "price" || citation.kind === "relationship") {
    return ticker ? `/companies?search=${encodeURIComponent(ticker)}` : "/companies";
  }
  return ticker ? `/companies?search=${encodeURIComponent(ticker)}` : null;
}

export function AIChatPanel({
  ticker,
  tradingMode = "paper",
}: {
  ticker?: string | null;
  tradingMode?: TradingMode;
}) {
  const [messages, setMessages] = useState<ChatPanelMessage[]>([]);
  const [input, setInput] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();
  const suggestedPrompts = useMemo(() => getSuggestedPrompts(ticker), [ticker]);

  const healthQuery = useQuery({
    queryKey: ["ai-health"],
    queryFn: getAIHealth,
    refetchInterval: 15000,
  });

  const sendMutation = useMutation({
    mutationFn: async ({
      message,
      conversation,
    }: {
      message: string;
      conversation: AIChatTurn[];
    }) =>
      sendAIChatMessage({
        message,
        ticker,
        tradingMode,
        conversation,
      }),
    onSuccess: (response) => {
      setMessages((prev) => [
        ...prev,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          content: response.answer,
          citations: response.citations,
          model: response.model,
        },
      ]);
    },
  });

  useEffect(() => {
    scrollRef.current?.scrollTo({
      top: scrollRef.current.scrollHeight,
      behavior: "smooth",
    });
  }, [messages, sendMutation.isPending]);

  const submitMessage = (rawText: string) => {
    const text = rawText.trim();
    if (!text || sendMutation.isPending) {
      return;
    }

    const conversation = messages.map((message) => ({
      role: message.role,
      content: message.content,
      citations: message.citations,
      model: message.model,
    }));

    setMessages((prev) => [
      ...prev,
      {
        id: crypto.randomUUID(),
        role: "user",
        content: text,
      },
    ]);
    setInput("");
    sendMutation.mutate({ message: text, conversation });
  };

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    submitMessage(input);
  };

  const notes = healthQuery.data?.notes ?? [];
  const gatewayLabel = healthQuery.data?.assistantLabel ?? "Local AI Gateway";
  const gatewayStatus = healthQuery.data?.status ?? "offline";

  return (
    <div className="terminal-card flex h-[560px] flex-col">
      <div className="flex items-center gap-2 border-b border-border px-4 py-3">
        <Bot className="h-4 w-4 text-primary" />
        <div>
          <h4 className="text-sm font-semibold text-foreground">AI Research Assistant</h4>
          <p className="text-[11px] text-muted-foreground">
            Grounded in StrattonAI events, studies, signals, and relationship context.
          </p>
        </div>
        <div
          className={`ml-auto rounded-full border px-2.5 py-1 text-[10px] font-medium uppercase tracking-[0.12em] ${healthTone(gatewayStatus)}`}
        >
          {gatewayLabel}
        </div>
      </div>

      <div ref={scrollRef} className="flex-1 space-y-3 overflow-y-auto p-4 scrollbar-thin">
        {messages.length === 0 ? (
          <div className="flex h-full flex-col items-center justify-center gap-4 text-center">
            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-primary/10">
              <Sparkles className="h-5 w-5 text-primary" />
            </div>
            <div className="space-y-2">
              <p className="text-sm font-medium text-foreground">Ask the StrattonAI Assistant</p>
              <p className="mx-auto max-w-xs text-xs text-muted-foreground">
                Responses stay grounded in the local research stack.
                {ticker ? ` Current focus: ${ticker}.` : " Select a ticker or ask a market-wide question."}
              </p>
            </div>
            <div className="flex max-w-md flex-wrap justify-center gap-2">
              {suggestedPrompts.map((prompt) => (
                <button
                  key={prompt}
                  onClick={() => submitMessage(prompt)}
                  disabled={sendMutation.isPending}
                  className="rounded-full border border-border px-3 py-1.5 text-xs text-muted-foreground transition-colors hover:bg-muted/50 hover:text-foreground disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {prompt}
                </button>
              ))}
            </div>
            {notes.length > 0 && (
              <div className="max-w-sm rounded-lg border border-border bg-muted/40 px-3 py-2 text-left">
                <div className="mb-1 flex items-center gap-2 text-[11px] font-medium uppercase tracking-[0.14em] text-muted-foreground">
                  <AlertTriangle className="h-3.5 w-3.5" />
                  Assistant status
                </div>
                <ul className="space-y-1 text-xs text-muted-foreground">
                  {notes.map((note) => (
                    <li key={note}>{note}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        ) : (
          <>
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex gap-2.5 ${message.role === "user" ? "justify-end" : "justify-start"}`}
              >
                {message.role === "assistant" && (
                  <div className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-md bg-primary/10">
                    <Bot className="h-3 w-3 text-primary" />
                  </div>
                )}
                <div
                  className={`max-w-[82%] rounded-lg px-3 py-2 text-xs leading-relaxed ${
                    message.role === "user"
                      ? "bg-primary/20 text-foreground"
                      : "bg-muted/50 text-foreground"
                  }`}
                >
                  <div className="whitespace-pre-wrap">{message.content}</div>
                  {message.role === "assistant" && message.citations && message.citations.length > 0 && (
                    <div className="mt-3 space-y-2 border-t border-border/70 pt-2">
                      <div className="text-[10px] font-medium uppercase tracking-[0.14em] text-muted-foreground">
                        Grounding
                      </div>
                      <div className="flex flex-wrap gap-2">
                        {message.citations.slice(0, 6).map((citation) => (
                          <button
                            key={`${citation.kind}:${citation.title}:${citation.detail}`}
                            onClick={() => {
                              const target = citationTarget(citation);
                              if (target) {
                                navigate(target);
                              }
                            }}
                            className="rounded-md border border-border bg-background/60 px-2 py-1 text-left hover:bg-muted/40"
                          >
                            <div className="flex items-center gap-1 text-[11px] font-medium text-foreground">
                              <ExternalLink className="h-3 w-3 text-muted-foreground" />
                              {citationLabel(citation)}
                            </div>
                            <div className="mt-1 text-[11px] text-muted-foreground">{citation.detail}</div>
                          </button>
                        ))}
                      </div>
                      {message.model && (
                        <div className="text-[10px] text-muted-foreground">Model: {message.model}</div>
                      )}
                    </div>
                  )}
                </div>
                {message.role === "user" && (
                  <div className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-md bg-muted">
                    <User className="h-3 w-3 text-muted-foreground" />
                  </div>
                )}
              </div>
            ))}
            {sendMutation.isPending && (
              <div className="flex gap-2.5">
                <div className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-md bg-primary/10">
                  <Bot className="h-3 w-3 text-primary" />
                </div>
                <div className="flex items-center gap-2 rounded-lg bg-muted/50 px-3 py-2 text-xs text-muted-foreground">
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                  Thinking through the current research context…
                </div>
              </div>
            )}
          </>
        )}
      </div>

      <form onSubmit={handleSubmit} className="flex items-center gap-2 border-t border-border px-4 py-3">
        <input
          type="text"
          value={input}
          onChange={(event) => setInput(event.target.value)}
          placeholder="Ask about a company, signal, catalyst, or research finding…"
          disabled={sendMutation.isPending}
          className="h-9 flex-1 rounded-md border border-border bg-muted/50 px-3 text-xs text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-ring disabled:cursor-not-allowed disabled:opacity-50"
        />
        <button
          type="submit"
          disabled={!input.trim() || sendMutation.isPending}
          className="flex h-9 w-9 items-center justify-center rounded-md bg-primary text-primary-foreground transition-colors hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-40"
        >
          {sendMutation.isPending ? (
            <Loader2 className="h-3.5 w-3.5 animate-spin" />
          ) : (
            <Send className="h-3.5 w-3.5" />
          )}
        </button>
      </form>
    </div>
  );
}
