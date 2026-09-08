"use client";

// Editor de redação com correção ENEM e histórico de evolução (seção 7.1).
//
// Visual portado do pacote "AI Tutor Studio". No protótipo o painel lateral
// mostrava competências com valores fixos; aqui ele lê a última correção real
// do aluno, e cada barra é a nota do critério sobre os 200 pontos possíveis.

import { useEffect, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Sparkles } from "lucide-react";
import { api, ApiError, type EssayPublic } from "@/lib/api";
import { Reveal } from "@/components/nerv/Reveal";
import { ProgressBar } from "@/components/nerv/Cards";

const CRITERIOS: Record<string, string> = {
  C1: "Norma culta",
  C2: "Compreensão do tema",
  C3: "Argumentação",
  C4: "Mecanismos linguísticos",
  C5: "Proposta de intervenção",
};

// Cada competência do ENEM vale de 0 a 200; a barra mostra a fração disso.
const NOTA_MAXIMA_CRITERIO = 200;

export default function RedacaoPage() {
  const [theme, setTheme] = useState("");
  const [content, setContent] = useState("");
  const [result, setResult] = useState<EssayPublic | null>(null);
  const [history, setHistory] = useState<EssayPublic[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const wordCount = content.trim() ? content.trim().split(/\s+/).length : 0;

  useEffect(() => {
    api
      .listEssays()
      .then(setHistory)
      .catch(() => undefined);
  }, []);

  const submit = async () => {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const essay = await api.submitEssay(theme, content);
      setResult(essay);
      setHistory((prev) => [essay, ...prev]);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Falha na correção. Tente novamente.");
    } finally {
      setLoading(false);
    }
  };

  const ultima = result ?? history[0];
  const criteriosUltima = Object.entries(ultima?.notas_por_criterio ?? {});

  return (
    <div className="mx-auto w-full max-w-5xl px-4 pb-28 pt-8 md:pb-12">
      <Reveal>
        <h1 className="font-display text-3xl font-bold sm:text-4xl">
          Sua <span className="text-gradient">redação</span>, corrigida em minutos
        </h1>
        <p className="mt-2 text-sm text-muted-foreground">
          Escreva ou cole seu texto. O NERV corrige nos 5 critérios do ENEM e explica o que
          melhorar.
        </p>
      </Reveal>

      <div className="mt-6 grid gap-4 lg:grid-cols-[1.4fr_1fr]">
        <Reveal delay={0.08}>
          <div className="surface-card flex h-full flex-col p-5 sm:p-6">
            <input
              value={theme}
              onChange={(e) => setTheme(e.target.value)}
              placeholder="Tema da redação (ex.: Desafios da inclusão digital no Brasil)"
              className="w-full rounded-xl border border-border bg-surface-2/60 px-4 py-3 text-sm outline-none transition-colors duration-300 placeholder:text-muted-foreground focus:border-primary/60"
            />
            <textarea
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder="Escreva ou cole sua redação aqui..."
              className="mt-3 min-h-64 flex-1 resize-y rounded-2xl bg-surface-2/60 p-4 text-sm leading-relaxed outline-none transition-colors duration-300 placeholder:text-muted-foreground focus:ring-2 focus:ring-ring"
            />
            <div className="mt-4 flex flex-wrap items-center gap-3">
              <motion.button
                type="button"
                onClick={() => void submit()}
                whileTap={{ scale: 0.97 }}
                disabled={loading || theme.trim().length < 5 || content.trim().length < 200}
                className="focus-nice inline-flex items-center gap-2 rounded-full bg-primary px-5 py-3 text-sm font-semibold text-primary-foreground transition-opacity duration-300 disabled:opacity-40"
              >
                <Sparkles className="size-4" />
                {loading ? "Corrigindo, leva ~1 min..." : "Corrigir agora"}
              </motion.button>
              <span className="text-xs text-muted-foreground">
                {wordCount} {wordCount === 1 ? "palavra" : "palavras"}
                {content.trim().length < 200 ? " · mínimo ~200 caracteres" : ""}
              </span>
            </div>
            {error && (
              <p className="mt-3 text-sm text-destructive" role="alert">
                {error}
              </p>
            )}
          </div>
        </Reveal>

        <Reveal delay={0.16}>
          <div className="surface-card h-full p-5 sm:p-6">
            <p className="text-xs uppercase tracking-wide text-primary">
              {result ? "Correção agora" : "Última correção"}
            </p>
            {ultima ? (
              <>
                <p className="mt-2 font-display text-4xl font-bold text-primary">
                  {ultima.nota_total}
                </p>
                <p className="text-sm text-muted-foreground">de 1000 pontos</p>
                {ultima.nota_estimada_real_enem && (
                  <p className="mt-1 text-xs text-muted-foreground">
                    Estimativa no ENEM real: {ultima.nota_estimada_real_enem}
                  </p>
                )}
                <div className="mt-6 space-y-4">
                  {criteriosUltima.map(([c, nota]) => (
                    <ProgressBar
                      key={c}
                      label={CRITERIOS[c] ?? c}
                      value={Math.round((nota / NOTA_MAXIMA_CRITERIO) * 100)}
                    />
                  ))}
                </div>
              </>
            ) : (
              <p className="mt-3 text-sm leading-relaxed text-muted-foreground">
                Você ainda não enviou nenhuma redação. Assim que enviar a primeira, a nota por
                competência aparece aqui.
              </p>
            )}
          </div>
        </Reveal>
      </div>

      <AnimatePresence>
        {result ? (
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
            className="surface-card mt-6 space-y-6 p-5 sm:p-7"
          >
            <h2 className="font-display text-lg font-bold">O que o NERV viu no seu texto</h2>

            {result.analise_detalhada && (
              <div className="grid gap-5 md:grid-cols-2">
                <div>
                  <h3 className="text-sm font-bold text-primary">Pontos fortes</h3>
                  <ul className="mt-2 space-y-1.5 text-sm leading-relaxed text-muted-foreground">
                    {result.analise_detalhada.pontos_fortes.map((p, i) => (
                      <li key={i}>{p}</li>
                    ))}
                  </ul>
                </div>
                <div>
                  <h3 className="text-sm font-bold text-streak">O que dá para melhorar</h3>
                  <ul className="mt-2 space-y-1.5 text-sm leading-relaxed text-muted-foreground">
                    {result.analise_detalhada.pontos_fracos.map((p, i) => (
                      <li key={i}>{p}</li>
                    ))}
                  </ul>
                </div>
              </div>
            )}

            {result.analise_detalhada?.erros_gramaticais?.length ? (
              <details>
                <summary className="focus-nice cursor-pointer list-none text-sm font-semibold text-primary">
                  Correções de escrita ({result.analise_detalhada.erros_gramaticais.length})
                </summary>
                <ul className="mt-3 space-y-2 text-sm">
                  {result.analise_detalhada.erros_gramaticais.map((e, i) => (
                    <li key={i} className="rounded-2xl bg-surface-2/60 p-4">
                      <p className="text-destructive line-through">{e.trecho}</p>
                      <p className="mt-1 text-primary">{e.correcao}</p>
                      <p className="mt-1 text-xs text-muted-foreground">{e.erro}</p>
                    </li>
                  ))}
                </ul>
              </details>
            ) : null}

            {result.reescrita_sugerida && (
              <details>
                <summary className="focus-nice cursor-pointer list-none text-sm font-semibold text-primary">
                  Como esse trecho poderia ficar
                </summary>
                <p className="mt-3 whitespace-pre-wrap rounded-2xl bg-surface-2/60 p-4 text-sm leading-relaxed text-muted-foreground">
                  {result.reescrita_sugerida}
                </p>
              </details>
            )}

            {result.proximos_passos?.length ? (
              <div>
                <h3 className="text-sm font-bold">Próximos passos</h3>
                <ul className="mt-2 space-y-1.5 text-sm leading-relaxed text-muted-foreground">
                  {result.proximos_passos.map((p, i) => (
                    <li key={i}>{p}</li>
                  ))}
                </ul>
              </div>
            ) : null}
          </motion.div>
        ) : null}
      </AnimatePresence>

      {history.length > 0 && (
        <Reveal delay={0.24}>
          <div className="surface-card mt-6 p-5 sm:p-6">
            <h2 className="font-display font-bold">Suas redações</h2>
            <ul className="mt-3 space-y-2">
              {history.map((e) => (
                <li
                  key={e.id}
                  className="flex items-center justify-between gap-4 rounded-2xl bg-surface-2/50 px-4 py-3 text-sm"
                >
                  <span className="truncate text-muted-foreground">{e.theme}</span>
                  <span className="shrink-0 font-display font-bold text-primary">
                    {e.nota_total}
                  </span>
                </li>
              ))}
            </ul>
          </div>
        </Reveal>
      )}
    </div>
  );
}
