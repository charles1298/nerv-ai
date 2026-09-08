"use client";

// Interface de tutoria com streaming SSE (seção 7.1 do CLAUDE.md).
//
// O visual e as animações vêm do pacote "AI Tutor Studio". A diferença
// estrutural em relação ao protótipo: lá o envio resolvia uma Promise<string>
// com a resposta pronta; aqui a resposta chega em pedaços por SSE, então a
// bolha do assistente nasce vazia e vai sendo preenchida. O indicador
// "NERV está pensando" some no primeiro caractere, não no fim da resposta.

import { useEffect, useRef, useState } from "react";
import { motion } from "framer-motion";
import { ArrowUp, RotateCcw, Sparkle } from "lucide-react";
import { api, streamChat } from "@/lib/api";
import { useAuthStore } from "@/store/auth";
import { ImageUpload } from "./ImageUpload";
import { MessageBubble } from "./MessageBubble";

interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
}

const SUGESTOES = [
  "Explica fração de um jeito fácil",
  "Me ajuda na interpretação de texto",
  "Como funciona a fotossíntese?",
  "Quero treinar tabuada jogando",
];

let contador = 0;
const novoId = () => `m${++contador}`;

export function TutorChat() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [isThinking, setIsThinking] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  // Só acompanha o texto se o aluno estiver no fim da conversa. Se ele subiu
  // para reler algo, puxá-lo de volta a cada pedaço seria tirar a leitura da mão dele.
  const grudadoNoFim = useRef(true);

  const primeiroNome = useAuthStore((s) => s.user?.name?.split(" ")[0]) ?? "";

  useEffect(() => {
    api
      .createSession()
      .then((s) => setSessionId(s.id))
      .catch(() => setError("Não foi possível iniciar a sessão. Recarregue a página."));
  }, []);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  // Rolagem instantânea, não suave. Cada pedaço do stream dispara este efeito;
  // com `behavior: "smooth"` a animação reinicia dezenas de vezes por segundo e
  // nunca assenta — é isso que dá a sensação de a conversa ficar "puxando".
  useEffect(() => {
    if (!grudadoNoFim.current) return;
    const el = scrollRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [messages, isThinking]);

  const aoRolar = () => {
    const el = scrollRef.current;
    if (!el) return;
    const distanciaDoFim = el.scrollHeight - el.scrollTop - el.clientHeight;
    grudadoNoFim.current = distanciaDoFim < 80;
  };

  const send = async (texto: string) => {
    const content = texto.trim();
    if (!content || !sessionId || isThinking) return;

    setInput("");
    setError(null);
    setIsThinking(true);
    inputRef.current?.focus();
    // Quem acabou de perguntar quer ver a resposta, mesmo que estivesse lendo acima.
    grudadoNoFim.current = true;
    setMessages((prev) => [
      ...prev,
      { id: novoId(), role: "user", content },
      { id: novoId(), role: "assistant", content: "" },
    ]);

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
      // Remove a bolha vazia do assistente: bolha em branco confunde o aluno.
      setMessages((prev) => prev.slice(0, -1));
      setError("Falha ao gerar resposta. Tente novamente.");
    } finally {
      setIsThinking(false);
    }
  };

  const novaConversa = async () => {
    setMessages([]);
    setError(null);
    setInput("");
    // A sessão vive no servidor: limpar a tela sem abrir outra manteria todo o
    // histórico anterior dentro do contexto do tutor.
    try {
      const s = await api.createSession();
      setSessionId(s.id);
    } catch {
      setError("Não foi possível iniciar uma nova conversa.");
    }
  };

  const vazio = messages.length === 0;
  const aguardandoPrimeiroChunk = isThinking && messages[messages.length - 1]?.content === "";

  return (
    <div className="flex min-h-0 flex-1 flex-col">
      <div
        ref={scrollRef}
        onScroll={aoRolar}
        className="mx-auto flex w-full max-w-3xl flex-1 flex-col gap-4 overflow-y-auto px-4 pt-6"
      >
        {/* Sem AnimatePresence de propósito. A resposta chega por SSE e cada
            pedaço dispara um setMessages, então são dezenas de re-renders por
            segundo; a animação de saída era reiniciada a cada um e nunca
            concluía, deixando a tela de boas-vindas presa junto da conversa.
            A entrada continua animada — é ela que o aluno realmente vê. */}
        {vazio ? (
          <motion.div
            initial={{ opacity: 0, y: 14 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
            className="flex flex-1 flex-col items-center justify-center gap-4 py-8 text-center"
          >
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src="/nerv-avatar.png"
              alt="NERV, seu tutor"
              width={816}
              height={816}
              className="size-24 animate-float drop-shadow-[0_18px_40px_var(--glow)]"
            />
            <h1 className="text-2xl font-bold sm:text-3xl">
              Oi{primeiroNome ? `, ${primeiroNome}` : ""}! Eu sou o{" "}
              <span className="text-gradient">NERV</span>
            </h1>
            <p className="max-w-md text-sm leading-relaxed text-muted-foreground">
              Me conta o que você quer estudar hoje. Pode ser dúvida de prova, exercício ou só
              curiosidade.
            </p>
            <div className="flex flex-wrap justify-center gap-2 pt-2">
              {SUGESTOES.map((s, i) => (
                <motion.button
                  key={s}
                  type="button"
                  onClick={() => void send(s)}
                  disabled={!sessionId}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.1 + i * 0.07, duration: 0.4 }}
                  whileHover={{ y: -2 }}
                  className="focus-nice inline-flex items-center gap-1.5 rounded-full border border-border bg-surface/70 px-3.5 py-2 text-sm text-muted-foreground transition-colors duration-300 hover:border-primary/40 hover:text-foreground disabled:opacity-50"
                >
                  <Sparkle className="size-3.5 text-primary" />
                  {s}
                </motion.button>
              ))}
            </div>
          </motion.div>
        ) : null}

        <div className="flex flex-col gap-4">
          {/* Sem AnimatePresence: MessageBubble é componente próprio, não um
              motion direto, então a saída nunca seria rastreada — e ao limpar a
              conversa o AnimatePresence ficaria esperando um callback que não
              chega, prendendo as bolhas antigas na tela. Cada bolha anima a
              própria entrada. */}
          {messages.map((m) =>
            // A bolha do assistente só entra quando o texto começa a chegar;
            // até lá quem representa a espera é o indicador logo abaixo.
            m.role === "assistant" && m.content === "" ? null : (
              <MessageBubble key={m.id} role={m.role} content={m.content} />
            ),
          )}

          {aguardandoPrimeiroChunk ? (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="flex items-center gap-3"
            >
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src="/nerv-avatar.png"
                alt=""
                width={816}
                height={816}
                className="size-8 shrink-0"
              />
              <span className="shimmer-text text-sm font-medium">NERV está pensando</span>
              <span className="flex items-end gap-1 pb-0.5">
                {[0, 1, 2].map((i) => (
                  <span
                    key={i}
                    className="size-1.5 animate-dot rounded-full bg-primary"
                    style={{ animationDelay: `${i * 0.15}s` }}
                  />
                ))}
              </span>
            </motion.div>
          ) : null}

          {error ? (
            <p className="text-sm text-destructive" role="alert">
              {error}
            </p>
          ) : null}
        </div>

        <div className="h-2" />
      </div>

      {/* Composer */}
      <div className="sticky bottom-0 mt-4 bg-gradient-to-t from-background via-background/95 to-transparent px-4 pb-24 pt-4 md:pb-6">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            void send(input);
          }}
          className="shadow-lift mx-auto flex w-full max-w-3xl items-end gap-2 rounded-3xl border border-border bg-surface/85 p-2 backdrop-blur-xl transition-colors duration-300 focus-within:border-primary/50"
        >
          <textarea
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                void send(input);
              }
            }}
            rows={1}
            placeholder="Escreva sua dúvida..."
            className="max-h-40 min-h-11 flex-1 resize-none bg-transparent px-3 py-2.5 text-sm outline-none placeholder:text-muted-foreground"
          />
          <ImageUpload
            sessionId={sessionId}
            disabled={isThinking || !sessionId}
            currentPrompt={input}
            onUploadStart={() => {
              setError(null);
              setMessages((prev) => [
                ...prev,
                {
                  id: novoId(),
                  role: "user",
                  content: input.trim() || "Enviei uma foto para análise.",
                },
              ]);
              setInput("");
            }}
            onAnalysis={(analysis) =>
              setMessages((prev) => [
                ...prev,
                { id: novoId(), role: "assistant", content: analysis },
              ])
            }
            onError={(message) => setError(message)}
          />
          <motion.button
            type="submit"
            aria-label="Enviar"
            disabled={!input.trim() || isThinking || !sessionId}
            whileTap={{ scale: 0.92 }}
            className="focus-nice grid size-11 shrink-0 place-items-center rounded-2xl bg-primary text-primary-foreground transition-opacity duration-300 disabled:opacity-40"
          >
            <ArrowUp className="size-5" />
          </motion.button>
        </form>

        {!vazio ? (
          <div className="mx-auto mt-2 flex w-full max-w-3xl justify-end">
            <button
              type="button"
              onClick={() => void novaConversa()}
              className="focus-nice inline-flex items-center gap-1.5 rounded-full px-2 py-1 text-xs text-muted-foreground transition-colors hover:text-foreground"
            >
              <RotateCcw className="size-3.5" /> Nova conversa
            </button>
          </div>
        ) : null}
      </div>
    </div>
  );
}
