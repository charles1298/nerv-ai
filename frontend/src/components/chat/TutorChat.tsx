"use client";

// Interface de tutoria com streaming SSE (seção 7.1 do CLAUDE.md).

import { useEffect, useRef, useState } from "react";
import { api, streamChat } from "@/lib/api";
import { ImageUpload } from "./ImageUpload";
import { MessageBubble } from "./MessageBubble";

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export function TutorChat() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [isThinking, setIsThinking] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    api
      .createSession()
      .then((s) => setSessionId(s.id))
      .catch(() => setError("Não foi possível iniciar a sessão. Recarregue a página."));
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isThinking]);

  const send = async () => {
    const content = input.trim();
    if (!content || !sessionId || isThinking) return;

    setInput("");
    setError(null);
    setIsThinking(true);
    setMessages((prev) => [...prev, { role: "user", content }, { role: "assistant", content: "" }]);

    try {
      await streamChat(sessionId, content, (chunk) => {
        setMessages((prev) => {
          const next = [...prev];
          const last = next[next.length - 1];
          next[next.length - 1] = { ...last, content: last.content + chunk };
          return next;
        });
      });
    } catch {
      setMessages((prev) => prev.slice(0, -1));
      setError("Falha ao gerar resposta. Tente novamente.");
    } finally {
      setIsThinking(false);
    }
  };

  return (
    <div className="flex h-full flex-col">
      <div className="flex-1 space-y-4 overflow-y-auto p-4">
        {messages.length === 0 && (
          <div className="mt-20 text-center text-nerv-muted">
            <p className="font-display text-xl">Oi! Eu sou o NERV. 👋</p>
            <p className="mt-2 text-sm">
              Me conta o que você quer estudar hoje — pode ser dúvida de prova, exercício ou
              só curiosidade.
            </p>
          </div>
        )}
        {messages.map((m, i) => (
          <MessageBubble key={i} role={m.role} content={m.content} />
        ))}
        {isThinking && messages[messages.length - 1]?.content === "" && (
          <p className="animate-pulse text-sm text-nerv-neon">NERV está pensando...</p>
        )}
        {error && <p className="text-sm text-red-400">{error}</p>}
        <div ref={bottomRef} />
      </div>

      <div className="border-t border-nerv-border p-4">
        <div className="flex gap-2">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                void send();
              }
            }}
            rows={1}
            placeholder="Digite sua dúvida..."
            className="flex-1 resize-none rounded-xl border border-nerv-border bg-nerv-surface px-4 py-3 text-sm outline-none focus:border-nerv-purple"
          />
          <ImageUpload
            sessionId={sessionId}
            disabled={isThinking || !sessionId}
            currentPrompt={input}
            onUploadStart={() => {
              setError(null);
              setMessages((prev) => [
                ...prev,
                { role: "user", content: input.trim() || "📷 Enviei uma foto para análise." },
              ]);
              setInput("");
            }}
            onAnalysis={(analysis) =>
              setMessages((prev) => [...prev, { role: "assistant", content: analysis }])
            }
            onError={(message) => setError(message)}
          />
          <button
            onClick={() => void send()}
            disabled={isThinking || !sessionId}
            className="rounded-xl bg-nerv-purple px-5 font-display font-medium transition hover:bg-nerv-purple-dim disabled:opacity-50"
          >
            Enviar
          </button>
        </div>
      </div>
    </div>
  );
}
