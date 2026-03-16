import { useState, useCallback, useRef, useEffect } from "react";
import { Send, Bot, User, Sparkles } from "lucide-react";

interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
}

const suggestedPrompts = [
  "Summarize the bullish case for NVDA",
  "Show key risks for AAPL",
  "What research supports a TSLA paper trade?",
  "Compare AMD vs NVDA over the next 10D horizon",
];

export function AIChatPanel() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages]);

  const sendMessage = useCallback(
    (text: string) => {
      if (!text.trim()) return;
      const userMsg: ChatMessage = { id: crypto.randomUUID(), role: "user", content: text.trim() };
      const botMsg: ChatMessage = {
        id: crypto.randomUUID(),
        role: "assistant",
        content: "This assistant is not yet connected to a backend. Once wired, responses will be grounded in StrattonAI research data, event studies, and signal scores.",
      };
      setMessages((prev) => [...prev, userMsg, botMsg]);
      setInput("");
    },
    [],
  );

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    sendMessage(input);
  };

  return (
    <div className="terminal-card flex flex-col h-[480px]">
      {/* Header */}
      <div className="px-4 py-3 border-b border-border flex items-center gap-2">
        <Bot className="h-4 w-4 text-primary" />
        <h4 className="text-sm font-semibold text-foreground">AI Research Assistant</h4>
        <span className="ml-auto text-xs text-muted-foreground">Shell · not connected</span>
      </div>

      {/* Messages */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto p-4 space-y-3 scrollbar-thin">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full gap-4 text-center">
            <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center">
              <Sparkles className="h-5 w-5 text-primary" />
            </div>
            <div>
              <p className="text-sm font-medium text-foreground">Ask the StrattonAI Assistant</p>
              <p className="text-xs text-muted-foreground mt-1 max-w-xs">
                Responses will be grounded in research data, event studies, and scored signals.
              </p>
            </div>
            <div className="flex flex-wrap gap-2 justify-center max-w-md">
              {suggestedPrompts.map((prompt) => (
                <button
                  key={prompt}
                  onClick={() => sendMessage(prompt)}
                  className="text-xs px-3 py-1.5 rounded-full border border-border text-muted-foreground hover:text-foreground hover:bg-muted/50 transition-colors"
                >
                  {prompt}
                </button>
              ))}
            </div>
          </div>
        ) : (
          messages.map((msg) => (
            <div key={msg.id} className={`flex gap-2.5 ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
              {msg.role === "assistant" && (
                <div className="w-6 h-6 rounded-md bg-primary/10 flex items-center justify-center shrink-0 mt-0.5">
                  <Bot className="h-3 w-3 text-primary" />
                </div>
              )}
              <div
                className={`max-w-[80%] px-3 py-2 rounded-lg text-xs leading-relaxed ${
                  msg.role === "user"
                    ? "bg-primary/20 text-foreground"
                    : "bg-muted/50 text-foreground"
                }`}
              >
                {msg.content}
              </div>
              {msg.role === "user" && (
                <div className="w-6 h-6 rounded-md bg-muted flex items-center justify-center shrink-0 mt-0.5">
                  <User className="h-3 w-3 text-muted-foreground" />
                </div>
              )}
            </div>
          ))
        )}
      </div>

      {/* Input */}
      <form onSubmit={handleSubmit} className="px-4 py-3 border-t border-border flex items-center gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask about a company, signal, or research finding…"
          className="flex-1 h-8 px-3 rounded-md bg-muted/50 border border-border text-xs text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-ring"
        />
        <button
          type="submit"
          disabled={!input.trim()}
          className="h-8 w-8 rounded-md bg-primary text-primary-foreground flex items-center justify-center disabled:opacity-40 hover:bg-primary/90 transition-colors"
        >
          <Send className="h-3.5 w-3.5" />
        </button>
      </form>
    </div>
  );
}
