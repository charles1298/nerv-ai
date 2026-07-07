"use client";

// Editor de redação com correção ENEM e histórico de evolução (seção 7.1).

import { useEffect, useState } from "react";
import { api, ApiError, type EssayPublic } from "@/lib/api";

const CRITERIOS: Record<string, string> = {
  C1: "Norma culta",
  C2: "Compreensão do tema",
  C3: "Argumentação",
  C4: "Mecanismos linguísticos",
  C5: "Proposta de intervenção",
};

export default function RedacaoPage() {
  const [theme, setTheme] = useState("");
  const [content, setContent] = useState("");
  const [result, setResult] = useState<EssayPublic | null>(null);
  const [history, setHistory] = useState<EssayPublic[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const wordCount = content.trim() ? content.trim().split(/\s+/).length : 0;

  useEffect(() => {
    api.listEssays().then(setHistory).catch(() => undefined);
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

  return (
    <div className="mx-auto max-w-4xl space-y-6 p-6">
      <h1 className="font-display text-2xl font-bold">Redação ENEM</h1>

      <div className="space-y-3 rounded-2xl border border-nerv-border bg-nerv-surface p-6">
        <input
          value={theme}
          onChange={(e) => setTheme(e.target.value)}
          placeholder="Tema da redação (ex.: Desafios da inclusão digital no Brasil)"
          className="w-full rounded-lg border border-nerv-border bg-nerv-bg px-3 py-2 text-sm outline-none focus:border-nerv-purple"
        />
        <textarea
          value={content}
          onChange={(e) => setContent(e.target.value)}
          rows={14}
          placeholder="Escreva sua redação aqui (mínimo ~200 caracteres)..."
          className="w-full resize-y rounded-lg border border-nerv-border bg-nerv-bg px-3 py-2 text-sm leading-relaxed outline-none focus:border-nerv-purple"
        />
        <div className="flex items-center justify-between">
          <span className="text-xs text-nerv-muted">{wordCount} palavras</span>
          <button
            onClick={() => void submit()}
            disabled={loading || theme.length < 5 || content.length < 200}
            className="rounded-lg bg-nerv-purple px-5 py-2 font-display text-sm font-medium transition hover:bg-nerv-purple-dim disabled:opacity-50"
          >
            {loading ? "Corrigindo (pode levar ~1 min)..." : "Enviar para correção"}
          </button>
        </div>
        {error && <p className="text-sm text-red-400">{error}</p>}
      </div>

      {result && (
        <div className="space-y-4 rounded-2xl border border-nerv-purple/50 bg-nerv-surface p-6">
          <div className="flex items-baseline justify-between">
            <h2 className="font-display text-lg font-bold">Resultado</h2>
            <p className="font-display text-4xl font-bold text-nerv-neon">
              {result.nota_total}
              <span className="text-base text-nerv-muted">/1000</span>
            </p>
          </div>
          {result.nota_estimada_real_enem && (
            <p className="text-sm text-nerv-muted">
              Estimativa no ENEM real: {result.nota_estimada_real_enem}
            </p>
          )}

          <div className="grid grid-cols-2 gap-2 md:grid-cols-5">
            {Object.entries(result.notas_por_criterio ?? {}).map(([c, nota]) => (
              <div key={c} className="rounded-lg border border-nerv-border p-3 text-center">
                <p className="text-[10px] text-nerv-muted">
                  {c} — {CRITERIOS[c] ?? ""}
                </p>
                <p className="font-display text-xl font-bold">{nota}</p>
              </div>
            ))}
          </div>

          {result.analise_detalhada && (
            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <h3 className="text-sm font-bold text-nerv-neon">Pontos fortes</h3>
                <ul className="mt-1 list-inside list-disc text-sm text-nerv-muted">
                  {result.analise_detalhada.pontos_fortes.map((p, i) => (
                    <li key={i}>{p}</li>
                  ))}
                </ul>
              </div>
              <div>
                <h3 className="text-sm font-bold text-red-400">Pontos fracos</h3>
                <ul className="mt-1 list-inside list-disc text-sm text-nerv-muted">
                  {result.analise_detalhada.pontos_fracos.map((p, i) => (
                    <li key={i}>{p}</li>
                  ))}
                </ul>
              </div>
            </div>
          )}

          {result.analise_detalhada?.erros_gramaticais?.length ? (
            <details>
              <summary className="cursor-pointer text-sm text-nerv-purple">
                Erros gramaticais ({result.analise_detalhada.erros_gramaticais.length})
              </summary>
              <ul className="mt-2 space-y-2 text-sm">
                {result.analise_detalhada.erros_gramaticais.map((e, i) => (
                  <li key={i} className="rounded-lg border border-nerv-border p-3">
                    <p className="text-red-400 line-through">{e.trecho}</p>
                    <p className="text-nerv-neon">{e.correcao}</p>
                    <p className="text-xs text-nerv-muted">{e.erro}</p>
                  </li>
                ))}
              </ul>
            </details>
          ) : null}

          {result.reescrita_sugerida && (
            <details>
              <summary className="cursor-pointer text-sm text-nerv-purple">
                Reescrita sugerida
              </summary>
              <p className="mt-2 whitespace-pre-wrap rounded-lg border border-nerv-border p-3 text-sm text-nerv-muted">
                {result.reescrita_sugerida}
              </p>
            </details>
          )}

          {result.proximos_passos?.length ? (
            <div>
              <h3 className="text-sm font-bold">Próximos passos</h3>
              <ul className="mt-1 list-inside list-disc text-sm text-nerv-muted">
                {result.proximos_passos.map((p, i) => (
                  <li key={i}>{p}</li>
                ))}
              </ul>
            </div>
          ) : null}
        </div>
      )}

      {history.length > 0 && (
        <div className="rounded-2xl border border-nerv-border bg-nerv-surface p-6">
          <h2 className="font-display font-bold">Histórico</h2>
          <ul className="mt-3 space-y-2">
            {history.map((e) => (
              <li
                key={e.id}
                className="flex items-center justify-between rounded-lg border border-nerv-border px-4 py-2 text-sm"
              >
                <span className="truncate text-nerv-muted">{e.theme}</span>
                <span className="ml-4 font-display font-bold text-nerv-purple">
                  {e.nota_total}
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
