"use client";

// Visão da escola para o gestor: heatmap de desempenho + diagnóstico BNCC (seção 7.3).

import { useEffect, useState } from "react";
import { Download } from "lucide-react";
import { ApiError, api, type BnccDiagnostic, type SchoolOverview } from "@/lib/api";
import { Reveal } from "@/components/nerv/Reveal";
import { Metric, PageHead, Panel, PrimaryButton } from "@/components/nerv/ProfessorUI";
import { Building2, Users } from "lucide-react";

function heatColor(rate: number | null): string {
  if (rate === null) return "bg-surface-2";
  if (rate >= 0.8) return "bg-primary";
  if (rate >= 0.6) return "bg-xp/70";
  if (rate >= 0.4) return "bg-streak/70";
  return "bg-destructive/70";
}

export default function EscolaPage() {
  const [overview, setOverview] = useState<SchoolOverview | null>(null);
  const [bncc, setBncc] = useState<BnccDiagnostic[]>([]);
  const [downloading, setDownloading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.schoolOverview().then(setOverview).catch(() => setError("Falha ao carregar a escola."));
    api.bnccDiagnostic().then(setBncc).catch(() => undefined);
  }, []);

  const downloadPdf = async () => {
    setDownloading(true);
    setError(null);
    try {
      await api.schoolOverviewPdf();
    } catch (e) {
      // O modo demonstração explica a ausência do backend na própria mensagem.
      setError(e instanceof ApiError ? e.message : "Falha ao baixar o PDF da escola.");
    } finally {
      setDownloading(false);
    }
  };

  return (
    <div className="mx-auto w-full max-w-5xl space-y-4 px-4 pb-16 pt-8">
      <Reveal>
        <PageHead
          titulo={
            <>
              Visão da <span className="text-gradient">escola</span>
            </>
          }
          descricao="Panorama de uso, desempenho por série e matéria, e quanto da BNCC já foi dominado."
          acao={
            <PrimaryButton icon={Download} onClick={() => void downloadPdf()} disabled={downloading}>
              {downloading ? "Gerando PDF..." : "Baixar PDF"}
            </PrimaryButton>
          }
        />
      </Reveal>
      {error && (
        <p className="text-sm text-destructive" role="alert">
          {error}
        </p>
      )}

      {overview && (
        <div className="grid grid-cols-2 gap-3 sm:gap-4">
          <Metric
            label="Alunos cadastrados"
            value={overview.students_count}
            icon={Building2}
            tone="muted"
          />
          <Metric
            label="Ativos nos últimos 7 dias"
            value={overview.active_students_last_7_days}
            icon={Users}
            tone="primary"
          />
        </div>
      )}

      {overview && overview.heatmap.length > 0 && (
        <Panel titulo="Desempenho por série × matéria">
          <div className="mt-4 grid gap-2">
            {overview.heatmap.map((cell, i) => (
              <div key={i} className="flex items-center gap-3 text-sm">
                <span className="w-24 text-xs text-muted-foreground">{cell.grade ?? "—"}</span>
                <span className="w-40 truncate">{cell.subject}</span>
                <div className="flex-1 rounded-full bg-surface-2/60">
                  <div
                    className={`h-3 rounded-full ${heatColor(cell.correct_rate)}`}
                    style={{ width: `${Math.max((cell.correct_rate ?? 0) * 100, 4)}%` }}
                  />
                </div>
                <span className="w-12 text-right text-xs text-muted-foreground">
                  {cell.correct_rate !== null ? `${Math.round(cell.correct_rate * 100)}%` : "—"}
                </span>
              </div>
            ))}
          </div>
        </Panel>
      )}

      {bncc.length > 0 && (
        <Panel titulo="Diagnóstico BNCC">
          <p className="-mt-2 mb-3 text-xs text-muted-foreground">% de habilidades dominadas por matéria</p>
          <div className="mt-4 space-y-3">
            {bncc.map((d) => (
              <div key={d.subject} className="flex items-center gap-3 text-sm">
                <span className="w-48 truncate">
                  {d.subject}{" "}
                  <span className="text-xs text-muted-foreground">({d.bncc_code ?? "—"})</span>
                </span>
                <div className="flex-1 rounded-full bg-surface-2/60">
                  <div
                    className="h-3 rounded-full bg-primary"
                    style={{ width: `${Math.max(d.mastery_pct, 2)}%` }}
                  />
                </div>
                <span className="w-24 text-right text-xs text-muted-foreground">
                  {d.topics_mastered}/{d.topics_total} ({d.mastery_pct}%)
                </span>
              </div>
            ))}
          </div>
        </Panel>
      )}
    </div>
  );
}
