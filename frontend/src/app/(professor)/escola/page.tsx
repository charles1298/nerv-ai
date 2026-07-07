"use client";

// Visão da escola para o gestor: heatmap de desempenho + diagnóstico BNCC (seção 7.3).

import { useEffect, useState } from "react";
import { api, type BnccDiagnostic, type SchoolOverview } from "@/lib/api";

function heatColor(rate: number | null): string {
  if (rate === null) return "bg-nerv-border";
  if (rate >= 0.8) return "bg-nerv-neon/70";
  if (rate >= 0.6) return "bg-nerv-purple/70";
  if (rate >= 0.4) return "bg-yellow-500/70";
  return "bg-red-500/70";
}

export default function EscolaPage() {
  const [overview, setOverview] = useState<SchoolOverview | null>(null);
  const [bncc, setBncc] = useState<BnccDiagnostic[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.schoolOverview().then(setOverview).catch(() => setError("Falha ao carregar a escola."));
    api.bnccDiagnostic().then(setBncc).catch(() => undefined);
  }, []);

  return (
    <div className="mx-auto max-w-5xl space-y-6 p-6">
      <h1 className="font-display text-2xl font-bold">Visão da Escola</h1>
      {error && <p className="text-sm text-red-400">{error}</p>}

      {overview && (
        <div className="grid grid-cols-2 gap-4">
          <div className="rounded-2xl border border-nerv-border bg-nerv-surface p-5">
            <p className="text-xs text-nerv-muted">Alunos cadastrados</p>
            <p className="mt-1 font-display text-3xl font-bold">{overview.students_count}</p>
          </div>
          <div className="rounded-2xl border border-nerv-border bg-nerv-surface p-5">
            <p className="text-xs text-nerv-muted">Ativos nos últimos 7 dias</p>
            <p className="mt-1 font-display text-3xl font-bold text-nerv-neon">
              {overview.active_students_last_7_days}
            </p>
          </div>
        </div>
      )}

      {overview && overview.heatmap.length > 0 && (
        <div className="rounded-2xl border border-nerv-border bg-nerv-surface p-6">
          <h2 className="font-display font-bold">Desempenho por série × matéria</h2>
          <div className="mt-4 grid gap-2">
            {overview.heatmap.map((cell, i) => (
              <div key={i} className="flex items-center gap-3 text-sm">
                <span className="w-24 text-xs text-nerv-muted">{cell.grade ?? "—"}</span>
                <span className="w-40 truncate">{cell.subject}</span>
                <div className="flex-1 rounded-full bg-nerv-bg">
                  <div
                    className={`h-3 rounded-full ${heatColor(cell.correct_rate)}`}
                    style={{ width: `${Math.max((cell.correct_rate ?? 0) * 100, 4)}%` }}
                  />
                </div>
                <span className="w-12 text-right text-xs text-nerv-muted">
                  {cell.correct_rate !== null ? `${Math.round(cell.correct_rate * 100)}%` : "—"}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {bncc.length > 0 && (
        <div className="rounded-2xl border border-nerv-border bg-nerv-surface p-6">
          <h2 className="font-display font-bold">Diagnóstico BNCC</h2>
          <p className="text-xs text-nerv-muted">% de habilidades dominadas por matéria</p>
          <div className="mt-4 space-y-3">
            {bncc.map((d) => (
              <div key={d.subject} className="flex items-center gap-3 text-sm">
                <span className="w-48 truncate">
                  {d.subject}{" "}
                  <span className="text-xs text-nerv-muted">({d.bncc_code ?? "—"})</span>
                </span>
                <div className="flex-1 rounded-full bg-nerv-bg">
                  <div
                    className="h-3 rounded-full bg-nerv-purple"
                    style={{ width: `${Math.max(d.mastery_pct, 2)}%` }}
                  />
                </div>
                <span className="w-24 text-right text-xs text-nerv-muted">
                  {d.topics_mastered}/{d.topics_total} ({d.mastery_pct}%)
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
