"use client";

// Dashboard da turma: cards por aluno ordenados por necessidade de intervenção (seção 7.2).

import { useEffect, useState } from "react";
import { api, type StudentCard, type StudentReport } from "@/lib/api";

const STATUS_STYLE: Record<StudentCard["status"], string> = {
  critico: "border-red-500/60 bg-red-500/5",
  atencao: "border-yellow-500/60 bg-yellow-500/5",
  em_dia: "border-nerv-neon/40 bg-nerv-neon/5",
};

const STATUS_LABEL: Record<StudentCard["status"], string> = {
  critico: "🔴 Crítico",
  atencao: "🟡 Atenção",
  em_dia: "🟢 Em dia",
};

export default function TurmaPage() {
  const [cards, setCards] = useState<StudentCard[]>([]);
  const [report, setReport] = useState<StudentReport | null>(null);
  const [loadingReport, setLoadingReport] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.classDashboard().then(setCards).catch(() => setError("Falha ao carregar a turma."));
  }, []);

  const openReport = async (studentId: string) => {
    setLoadingReport(studentId);
    setReport(null);
    try {
      setReport(await api.studentReport(studentId));
    } catch {
      setError("Falha ao gerar relatório do aluno.");
    } finally {
      setLoadingReport(null);
    }
  };

  return (
    <div className="mx-auto max-w-5xl space-y-6 p-6">
      <h1 className="font-display text-2xl font-bold">Dashboard da Turma</h1>
      {error && <p className="text-sm text-red-400">{error}</p>}

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {cards.map((c) => (
          <div
            key={c.student_id}
            className={`rounded-2xl border p-5 ${STATUS_STYLE[c.status]}`}
          >
            <div className="flex items-center justify-between">
              <p className="font-display font-bold">{c.name}</p>
              <span className="text-xs">{STATUS_LABEL[c.status]}</span>
            </div>
            <p className="text-xs text-nerv-muted">{c.grade ?? "série não informada"}</p>
            <div className="mt-3 space-y-1 text-xs text-nerv-muted">
              <p>Sessões: {c.sessions_count} · Exercícios: {c.exercises_attempted}</p>
              <p>
                Taxa de acerto:{" "}
                {c.correct_rate !== null ? `${Math.round(c.correct_rate * 100)}%` : "—"}
              </p>
              {c.struggling_topics.length > 0 && (
                <p className="text-red-400">Dificuldade: {c.struggling_topics.join(", ")}</p>
              )}
            </div>
            <button
              onClick={() => void openReport(c.student_id)}
              disabled={loadingReport === c.student_id}
              className="mt-3 w-full rounded-lg bg-nerv-purple px-3 py-1.5 font-display text-xs font-medium transition hover:bg-nerv-purple-dim disabled:opacity-50"
            >
              {loadingReport === c.student_id ? "Gerando relatório..." : "Relatório completo"}
            </button>
          </div>
        ))}
        {cards.length === 0 && !error && (
          <p className="text-sm text-nerv-muted">Nenhum aluno cadastrado ainda.</p>
        )}
      </div>

      {report && (
        <div className="rounded-2xl border border-nerv-purple/50 bg-nerv-surface p-6">
          <div className="flex items-center justify-between">
            <h2 className="font-display text-lg font-bold">
              Relatório — {report.student.name}
            </h2>
            <button
              onClick={() => setReport(null)}
              className="text-sm text-nerv-muted hover:text-nerv-text"
            >
              fechar ✕
            </button>
          </div>
          {report.narrative ? (
            <div className="mt-4 space-y-4 text-sm">
              <p>{report.narrative.resumo}</p>
              <p className="text-nerv-muted">{report.narrative.evolucao}</p>
              <div className="grid gap-4 md:grid-cols-2">
                <div>
                  <h3 className="font-bold text-nerv-neon">Pontos fortes</h3>
                  <ul className="mt-1 list-inside list-disc text-nerv-muted">
                    {report.narrative.pontos_fortes.map((p, i) => (
                      <li key={i}>{p}</li>
                    ))}
                  </ul>
                </div>
                <div>
                  <h3 className="font-bold text-yellow-400">Pontos de atenção</h3>
                  <ul className="mt-1 list-inside list-disc text-nerv-muted">
                    {report.narrative.pontos_atencao.map((p, i) => (
                      <li key={i}>{p}</li>
                    ))}
                  </ul>
                </div>
              </div>
              <div>
                <h3 className="font-bold">Recomendações</h3>
                <ul className="mt-1 list-inside list-disc text-nerv-muted">
                  {report.narrative.recomendacoes.map((p, i) => (
                    <li key={i}>{p}</li>
                  ))}
                </ul>
              </div>
            </div>
          ) : (
            <p className="mt-4 text-sm text-nerv-muted">
              Narrativa indisponível no momento — os dados quantitativos estão nos cards acima.
            </p>
          )}
        </div>
      )}
    </div>
  );
}
