"use client";

// Resolução de exercícios com explicação (seções 5.7 e 7.1).
//
// A ordem da tela é deliberada: antes dos passos vem "o que eu entendi". Na foto
// a leitura pode divergir do papel, e o aluno precisa perceber isso ANTES de
// estudar a resolução de um exercício que não é o dele.
//
// A resposta final fica depois dos passos, não antes. Quem só quer copiar rola
// até o fim e copia; quem quer aprender lê o caminho. É o mínimo que dá para
// fazer numa tela que, por definição do entregável, entrega a resposta.

import { useEffect, useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import {
  AlertTriangle,
  Camera,
  CheckCircle2,
  Eye,
  Lightbulb,
  ListChecks,
  Loader2,
  Repeat,
  Sparkles,
  Target,
  Trash2,
  Type,
} from "lucide-react";
import {
  ApiError,
  api,
  resolverExercicioPorFoto,
  type ConfiancaResolucao,
  type ResolucaoPublic,
  type ResolucaoResumo,
} from "@/lib/api";
import { MathRenderer } from "@/components/chat/MathRenderer";
import { Reveal } from "@/components/nerv/Reveal";

const TAMANHO_MAXIMO = 5 * 1024 * 1024;

const AVISO_CONFIANCA: Record<ConfiancaResolucao, string | null> = {
  alta: null,
  media: "Li o enunciado, mas fiquei com alguma dúvida. Confira abaixo se é isso mesmo.",
  baixa:
    "Tive dificuldade para ler o enunciado. Confira o que entendi antes de seguir — se estiver errado, tente uma foto mais nítida ou digite a questão.",
};

function formataData(iso: string) {
  return new Date(iso).toLocaleDateString("pt-BR", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}

export default function ResolverPage() {
  const [modo, setModo] = useState<"texto" | "foto">("texto");
  const [enunciado, setEnunciado] = useState("");
  const [duvida, setDuvida] = useState("");
  const [arquivo, setArquivo] = useState<File | null>(null);

  const [resolucao, setResolucao] = useState<ResolucaoPublic | null>(null);
  const [historico, setHistorico] = useState<ResolucaoResumo[]>([]);
  const [resolvendo, setResolvendo] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const inputArquivo = useRef<HTMLInputElement>(null);

  useEffect(() => {
    api
      .listResolucoes()
      .then(setHistorico)
      .catch(() => undefined);
  }, []);

  const podeEnviar =
    modo === "texto" ? enunciado.trim().length >= 10 : arquivo !== null;

  const registraNoHistorico = (r: ResolucaoPublic) =>
    setHistorico((prev) => [
      {
        id: r.id,
        origem: r.origem,
        materia: r.materia,
        topico: r.topico,
        enunciado_interpretado: r.enunciado_interpretado,
        resposta_final: r.resposta_final,
        created_at: r.created_at,
      },
      ...prev,
    ]);

  const resolver = async () => {
    if (!podeEnviar || resolvendo) return;
    setResolvendo(true);
    setError(null);
    try {
      const r =
        modo === "texto"
          ? await api.resolverExercicio(enunciado.trim(), duvida.trim())
          : await resolverExercicioPorFoto(arquivo as File, duvida.trim());
      setResolucao(r);
      registraNoHistorico(r);
    } catch (e) {
      setError(
        e instanceof ApiError ? e.message : "Não consegui resolver agora. Tente de novo.",
      );
    } finally {
      setResolvendo(false);
    }
  };

  const escolherArquivo = (f: File | undefined) => {
    if (!f) return;
    if (f.size > TAMANHO_MAXIMO) {
      setError("A imagem passa de 5 MB. Tente tirar a foto de novo, mais de perto.");
      return;
    }
    setError(null);
    setArquivo(f);
  };

  const abrir = async (id: string) => {
    setError(null);
    try {
      setResolucao(await api.getResolucao(id));
    } catch {
      setError("Não consegui abrir essa resolução.");
    }
  };

  const excluir = async (id: string) => {
    setError(null);
    try {
      await api.deleteResolucao(id);
      setHistorico((prev) => prev.filter((r) => r.id !== id));
      if (resolucao?.id === id) setResolucao(null);
    } catch {
      setError("Não consegui excluir essa resolução.");
    }
  };

  return (
    <div className="mx-auto w-full max-w-4xl px-4 pb-28 pt-8 md:pb-12">
      <Reveal>
        <h1 className="font-display text-3xl font-bold sm:text-4xl">
          Travou num <span className="text-gradient">exercício</span>?
        </h1>
        <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
          Manda a questão, digitada ou fotografada. Eu resolvo passo a passo e explico o porquê de
          cada um — para você conseguir fazer a próxima sozinho.
        </p>
      </Reveal>

      {/* ---------- entrada ---------- */}
      <Reveal delay={0.08}>
        <div className="surface-card mt-6 p-5 sm:p-7">
          <div className="flex gap-2">
            {(
              [
                { valor: "texto", label: "Digitar", icone: Type },
                { valor: "foto", label: "Fotografar", icone: Camera },
              ] as const
            ).map((op) => (
              <button
                key={op.valor}
                type="button"
                onClick={() => {
                  setModo(op.valor);
                  setError(null);
                }}
                className={`focus-nice inline-flex items-center gap-2 rounded-full border px-4 py-2 text-sm transition-colors duration-300 ${
                  modo === op.valor
                    ? "border-primary bg-primary/15 text-foreground"
                    : "border-border bg-surface/60 text-muted-foreground hover:border-primary/40 hover:text-foreground"
                }`}
              >
                <op.icone className="size-4" />
                {op.label}
              </button>
            ))}
          </div>

          {modo === "texto" ? (
            <textarea
              value={enunciado}
              onChange={(e) => setEnunciado(e.target.value)}
              placeholder="Cole ou digite o exercício aqui. Pode ser a questão inteira, do jeito que está na lista."
              className="mt-5 min-h-40 w-full resize-y rounded-2xl bg-surface-2/60 p-4 text-sm leading-relaxed outline-none transition-colors duration-300 placeholder:text-muted-foreground focus:ring-2 focus:ring-ring"
            />
          ) : (
            <div className="mt-5">
              <input
                ref={inputArquivo}
                type="file"
                accept="image/jpeg,image/png,image/webp,image/gif"
                className="hidden"
                onChange={(e) => escolherArquivo(e.target.files?.[0])}
              />
              <button
                type="button"
                onClick={() => inputArquivo.current?.click()}
                className="focus-nice flex min-h-40 w-full flex-col items-center justify-center gap-2 rounded-2xl border border-dashed border-border bg-surface-2/40 p-6 text-center transition-colors duration-300 hover:border-primary/50"
              >
                <Camera className="size-7 text-primary" />
                <span className="text-sm font-medium">
                  {arquivo ? arquivo.name : "Toque para escolher a foto do exercício"}
                </span>
                <span className="text-xs text-muted-foreground">
                  JPG, PNG ou WEBP, até 5 MB. Foto nítida e reta lê melhor.
                </span>
              </button>
            </div>
          )}

          <input
            value={duvida}
            onChange={(e) => setDuvida(e.target.value)}
            placeholder="Onde você travou? (opcional — ex.: não sei que fórmula usar)"
            className="mt-3 w-full rounded-xl border border-border bg-surface-2/60 px-4 py-3 text-sm outline-none transition-colors duration-300 placeholder:text-muted-foreground focus:border-primary/60"
          />

          <motion.button
            type="button"
            onClick={() => void resolver()}
            disabled={!podeEnviar || resolvendo}
            whileTap={{ scale: 0.97 }}
            className="focus-nice mt-5 inline-flex items-center gap-2 rounded-full bg-primary px-5 py-3 text-sm font-semibold text-primary-foreground transition-opacity duration-300 disabled:opacity-40"
          >
            {resolvendo ? (
              <Loader2 className="size-4 animate-spin" />
            ) : (
              <Sparkles className="size-4" />
            )}
            {resolvendo ? "Resolvendo..." : "Resolver e explicar"}
          </motion.button>

          {resolvendo && (
            <p className="shimmer-text mt-3 text-sm font-medium">
              {modo === "foto" ? "Lendo a foto e resolvendo" : "Montando a resolução passo a passo"}
            </p>
          )}

          {error && (
            <p className="mt-3 text-sm text-destructive" role="alert">
              {error}
            </p>
          )}
        </div>
      </Reveal>

      {/* ---------- resolução ---------- */}
      <AnimatePresence>
        {resolucao && (
          <motion.div
            key={resolucao.id}
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
            className="mt-6 space-y-4"
          >
            {/* O que o sistema entendeu vem ANTES dos passos, de propósito. */}
            <div className="surface-card p-5 sm:p-6">
              <div className="flex flex-wrap items-center gap-2">
                <span className="inline-flex items-center gap-1.5 rounded-full border border-border bg-primary/10 px-3 py-1 text-xs font-semibold text-primary">
                  {resolucao.materia}
                </span>
                <span className="inline-flex items-center rounded-full border border-border bg-surface-2/60 px-3 py-1 text-xs text-muted-foreground">
                  {resolucao.topico}
                </span>
              </div>

              <h2 className="mt-4 flex items-center gap-2 text-sm font-semibold">
                <Eye className="size-4 text-primary" /> O que eu entendi do exercício
              </h2>
              <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
                <MathRenderer content={resolucao.enunciado_interpretado} />
              </p>

              {AVISO_CONFIANCA[resolucao.confianca] && (
                <p className="mt-4 flex gap-2.5 rounded-2xl border border-streak/40 bg-streak/10 p-3.5 text-sm leading-relaxed text-foreground">
                  <AlertTriangle className="mt-0.5 size-4 shrink-0 text-streak" />
                  {AVISO_CONFIANCA[resolucao.confianca]}
                </p>
              )}
            </div>

            <div className="surface-card p-5 sm:p-7">
              <h2 className="flex items-center gap-2 font-display text-lg font-bold">
                <ListChecks className="size-5 text-primary" /> Passo a passo
              </h2>

              <ol className="mt-5 space-y-5">
                {resolucao.passos.map((passo) => (
                  <li key={passo.numero} className="flex gap-4">
                    <span className="grid size-8 shrink-0 place-items-center rounded-full bg-primary/15 font-display text-sm font-bold text-primary ring-1 ring-primary/30">
                      {passo.numero}
                    </span>
                    <div className="min-w-0 flex-1">
                      <p className="font-semibold">{passo.titulo}</p>
                      <p className="mt-1 text-sm leading-relaxed text-muted-foreground">
                        <MathRenderer content={passo.explicacao} />
                      </p>
                      {passo.expressao && (
                        <div className="mt-3 overflow-x-auto rounded-2xl bg-surface-2/60 px-4 py-3 text-base">
                          <MathRenderer content={passo.expressao} />
                        </div>
                      )}
                    </div>
                  </li>
                ))}
              </ol>

              <div className="glow-ring mt-7 rounded-2xl border border-primary/40 bg-primary/10 p-5">
                <p className="flex items-center gap-2 text-xs uppercase tracking-wide text-primary">
                  <CheckCircle2 className="size-4" /> Resposta
                </p>
                <p className="mt-2 font-display text-xl font-bold">
                  <MathRenderer content={resolucao.resposta_final} />
                </p>
              </div>
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <div className="surface-card p-5 sm:p-6">
                <h3 className="flex items-center gap-2 font-semibold">
                  <Lightbulb className="size-4 text-xp" /> O conceito por trás
                </h3>
                <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
                  <MathRenderer content={resolucao.conceito} />
                </p>
              </div>

              <div className="surface-card p-5 sm:p-6">
                <h3 className="flex items-center gap-2 font-semibold">
                  <Target className="size-4 text-primary" /> Como conferir sozinho
                </h3>
                <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
                  <MathRenderer content={resolucao.como_conferir} />
                </p>
              </div>
            </div>

            {resolucao.erros_comuns.length > 0 && (
              <div className="surface-card p-5 sm:p-6">
                <h3 className="flex items-center gap-2 font-semibold">
                  <AlertTriangle className="size-4 text-streak" /> Onde costuma escorregar
                </h3>
                <ul className="mt-3 space-y-2">
                  {resolucao.erros_comuns.map((erro, i) => (
                    <li
                      key={i}
                      className="flex gap-2.5 text-sm leading-relaxed text-muted-foreground"
                    >
                      <span aria-hidden className="mt-2 size-1.5 shrink-0 rounded-full bg-streak" />
                      <MathRenderer content={erro} />
                    </li>
                  ))}
                </ul>
              </div>
            )}

            <div className="surface-card p-5 sm:p-6">
              <h3 className="flex items-center gap-2 font-semibold">
                <Repeat className="size-4 text-badge" /> Agora tenta você
              </h3>
              <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
                <MathRenderer content={resolucao.exercicio_parecido} />
              </p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* ---------- histórico ---------- */}
      {historico.length > 0 && (
        <Reveal delay={0.16}>
          <div className="surface-card mt-6 p-5 sm:p-6">
            <h3 className="font-display font-bold">Exercícios que você já resolveu aqui</h3>
            <ul className="mt-3 space-y-2">
              {historico.map((r) => (
                <li
                  key={r.id}
                  className="flex items-center justify-between gap-3 rounded-2xl bg-surface-2/50 px-4 py-3"
                >
                  <button
                    type="button"
                    onClick={() => void abrir(r.id)}
                    className="focus-nice min-w-0 flex-1 text-left"
                  >
                    <span className="block truncate text-sm font-medium">
                      {r.enunciado_interpretado}
                    </span>
                    <span className="block text-xs text-muted-foreground">
                      {r.materia} · {r.topico} · {r.origem === "foto" ? "foto" : "digitado"} ·{" "}
                      {formataData(r.created_at)}
                    </span>
                  </button>
                  <button
                    type="button"
                    onClick={() => void excluir(r.id)}
                    aria-label={"Excluir resolução de " + r.topico}
                    className="focus-nice grid size-9 shrink-0 place-items-center rounded-xl text-muted-foreground transition-colors duration-300 hover:bg-destructive/10 hover:text-destructive"
                  >
                    <Trash2 className="size-4" />
                  </button>
                </li>
              ))}
            </ul>
          </div>
        </Reveal>
      )}
    </div>
  );
}
