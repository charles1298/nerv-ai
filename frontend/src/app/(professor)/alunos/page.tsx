"use client";

// Lista de alunos da turma com relatório individual (seção 7.2).
//
// O painel responde "quem precisa de mim"; esta tela responde "o que está
// acontecendo com este aluno". Por isso aqui cabe a lista inteira, com filtro e
// o relatório completo do agente.

import { useEffect, useMemo, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Download, FileText, Search, X } from "lucide-react";
import { ApiError, api, type StudentCard, type StudentReport } from "@/lib/api";
import { Reveal } from "@/components/nerv/Reveal";
import {
  GhostButton,
  PageHead,
  Panel,
  PrimaryButton,
  StatusPill,
  Tag,
} from "@/components/nerv/ProfessorUI";

type Filtro = "todos" | StudentCard["status"];

const FILTROS: { valor: Filtro; label: string }[] = [
  { valor: "todos", label: "Todos" },
  { valor: "critico", label: "Críticos" },
  { valor: "atencao", label: "Atenção" },
  { valor: "em_dia", label: "Em dia" },
];

export default function AlunosPage() {
  const [cards, setCards] = useState<StudentCard[]>([]);
  const [busca, setBusca] = useState("");
  const [filtro, setFiltro] = useState<Filtro>("todos");

  const [report, setReport] = useState<StudentReport | null>(null);
  const [gerando, setGerando] = useState<string | null>(null);
  const [baixando, setBaixando] = useState<string | null>(null);
  const [carregando, setCarregando] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .classDashboard()
      .then(setCards)
      .catch(() => setError("Falha ao carregar a turma."))
      .finally(() => setCarregando(false));
  }, []);

  const visiveis = useMemo(() => {
    const termo = busca.trim().toLowerCase();
    return cards
      .filter((c) => (filtro === "todos" ? true : c.status === filtro))
      .filter((c) => (termo ? c.name.toLowerCase().includes(termo) : true));
  }, [cards, busca, filtro]);

  const abrirRelatorio = async (studentId: string) => {
    setGerando(studentId);
    setReport(null);
    setError(null);
    try {
      setReport(await api.studentReport(studentId));
    } catch {
      setError("Falha ao gerar relatório do aluno.");
    } finally {
      setGerando(null);
    }
  };

  const baixarPdf = async (studentId: string, nome: string) => {
    setBaixando(studentId);
    setError(null);
    try {
      await api.studentReportPdf(studentId, nome);
    } catch (e) {
      // O modo demonstração explica a ausência do backend na própria mensagem.
      setError(e instanceof ApiError ? e.message : "Falha ao baixar o PDF do relatório.");
    } finally {
      setBaixando(null);
    }
  };

  return (
    <div className="mx-auto w-full max-w-6xl px-4 pb-16 pt-8">
      <Reveal>
        <PageHead
          titulo={
            <>
              Seus <span className="text-gradient">alunos</span>
            </>
          }
          descricao="Cada aluno com o que já fez, onde trava e o relatório pedagógico completo."
        />
      </Reveal>

      <Reveal delay={0.08}>
        <div className="mt-6 flex flex-wrap items-center gap-3">
          <div className="relative min-w-0 flex-1 sm:max-w-xs">
            <Search className="pointer-events-none absolute left-3.5 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
            <input
              value={busca}
              onChange={(e) => setBusca(e.target.value)}
              placeholder="Buscar por nome"
              aria-label="Buscar aluno por nome"
              className="w-full rounded-full border border-border bg-surface/60 py-2.5 pl-10 pr-4 text-sm outline-none transition-colors duration-300 placeholder:text-muted-foreground focus:border-primary/60"
            />
          </div>
          <div className="flex flex-wrap gap-2">
            {FILTROS.map((f) => (
              <button
                key={f.valor}
                type="button"
                onClick={() => setFiltro(f.valor)}
                className={`focus-nice rounded-full border px-3.5 py-2 text-sm transition-colors duration-300 ${
                  filtro === f.valor
                    ? "border-primary bg-primary/15 text-foreground"
                    : "border-border bg-surface/60 text-muted-foreground hover:border-primary/40 hover:text-foreground"
                }`}
              >
                {f.label}
              </button>
            ))}
          </div>
        </div>
      </Reveal>

      {error && (
        <p className="mt-6 text-sm text-destructive" role="alert">
          {error}
        </p>
      )}

      {carregando ? (
        <p className="shimmer-text mt-8 text-sm font-medium">Carregando seus alunos</p>
      ) : (
        <div className="mt-5 grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {visiveis.map((c, i) => (
            <Reveal key={c.student_id} delay={Math.min(0.04 * i, 0.3)}>
              <div className="surface-card surface-card-hover flex h-full flex-col p-5">
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <p className="truncate font-display font-bold">{c.name}</p>
                    <p className="text-xs text-muted-foreground">
                      {c.grade ?? "série não informada"}
                    </p>
                  </div>
                  <StatusPill status={c.status} />
                </div>

                <dl className="mt-4 grid grid-cols-3 gap-2 text-center">
                  <Numero rotulo="Sessões" valor={c.sessions_count} />
                  <Numero rotulo="Exercícios" valor={c.exercises_attempted} />
                  <Numero
                    rotulo="Acerto"
                    valor={c.correct_rate !== null ? `${Math.round(c.correct_rate * 100)}%` : "—"}
                  />
                </dl>

                {c.struggling_topics.length > 0 && (
                  <div className="mt-4">
                    <p className="text-xs text-muted-foreground">Trava em</p>
                    <div className="mt-1.5 flex flex-wrap gap-1.5">
                      {c.struggling_topics.slice(0, 3).map((t) => (
                        <Tag key={t}>{t}</Tag>
                      ))}
                    </div>
                  </div>
                )}

                <div className="mt-auto flex gap-2 pt-5">
                  <PrimaryButton
                    icon={FileText}
                    onClick={() => void abrirRelatorio(c.student_id)}
                    disabled={gerando === c.student_id}
                  >
                    {gerando === c.student_id ? "Gerando..." : "Relatório"}
                  </PrimaryButton>
                  <GhostButton
                    icon={Download}
                    onClick={() => void baixarPdf(c.student_id, c.name)}
                    disabled={baixando === c.student_id}
                    title={`Baixar relatório de ${c.name} em PDF`}
                  >
                    {baixando === c.student_id ? "..." : "PDF"}
                  </GhostButton>
                </div>
              </div>
            </Reveal>
          ))}

          {visiveis.length === 0 && !error && (
            <Panel className="md:col-span-2 lg:col-span-3">
              <p className="text-sm leading-relaxed text-muted-foreground">
                {cards.length === 0
                  ? "Nenhum aluno cadastrado ainda."
                  : "Nenhum aluno com esse filtro."}
              </p>
            </Panel>
          )}
        </div>
      )}

      <AnimatePresence>
        {report && (
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.4, ease: [0.22, 1, 0.36, 1] }}
            className="surface-card glow-ring mt-6 p-5 sm:p-7"
          >
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-xs uppercase tracking-wide text-primary">
                  Relatório pedagógico
                </p>
                <h2 className="mt-1 font-display text-xl font-bold">{report.student.name}</h2>
              </div>
              <button
                type="button"
                onClick={() => setReport(null)}
                aria-label="Fechar relatório"
                className="focus-nice grid size-9 shrink-0 place-items-center rounded-xl text-muted-foreground transition-colors duration-300 hover:bg-surface-2 hover:text-foreground"
              >
                <X className="size-4" />
              </button>
            </div>

            {report.narrative ? (
              <div className="mt-5 space-y-5 text-sm">
                <p className="leading-relaxed">{report.narrative.resumo}</p>
                <p className="leading-relaxed text-muted-foreground">{report.narrative.evolucao}</p>

                <div className="grid gap-5 md:grid-cols-2">
                  <Lista titulo="Pontos fortes" cor="text-primary" itens={report.narrative.pontos_fortes} />
                  <Lista
                    titulo="Pontos de atenção"
                    cor="text-streak"
                    itens={report.narrative.pontos_atencao}
                  />
                </div>

                <Lista
                  titulo="Recomendações"
                  cor="text-foreground"
                  itens={report.narrative.recomendacoes}
                />
              </div>
            ) : (
              <p className="mt-5 text-sm leading-relaxed text-muted-foreground">
                A narrativa do agente não veio desta vez. Os números dos cartões acima continuam
                válidos — eles vêm do banco, não do modelo.
              </p>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

function Numero({ rotulo, valor }: { rotulo: string; valor: string | number }) {
  return (
    <div className="rounded-xl bg-surface-2/50 py-2">
      <dt className="text-[0.65rem] uppercase tracking-wide text-muted-foreground">{rotulo}</dt>
      <dd className="font-display text-lg font-bold">{valor}</dd>
    </div>
  );
}

function Lista({ titulo, cor, itens }: { titulo: string; cor: string; itens: string[] }) {
  if (itens.length === 0) return null;
  return (
    <div>
      <h3 className={`text-sm font-bold ${cor}`}>{titulo}</h3>
      <ul className="mt-2 space-y-1.5">
        {itens.map((p, i) => (
          <li key={i} className="text-sm leading-relaxed text-muted-foreground">
            {p}
          </li>
        ))}
      </ul>
    </div>
  );
}
