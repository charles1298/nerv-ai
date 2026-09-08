"use client";

// Painel do professor (seção 7.2): visão da turma em números reais.
//
// Tudo aqui é derivado de /reports/turma. Nenhuma métrica é estimada: se o dado
// não existe, a tela diz que não existe em vez de exibir um número plausível.

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { AlertTriangle, ArrowUpRight, ListChecks, MessageCircle, Target, Users } from "lucide-react";
import { api, type StudentCard } from "@/lib/api";
import { Reveal } from "@/components/nerv/Reveal";
import { Bar, Metric, PageHead, Panel, StatusPill, Tag } from "@/components/nerv/ProfessorUI";

export default function PainelPage() {
  const [cards, setCards] = useState<StudentCard[]>([]);
  const [carregando, setCarregando] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .classDashboard()
      .then(setCards)
      .catch(() => setError("Falha ao carregar a turma."))
      .finally(() => setCarregando(false));
  }, []);

  const resumo = useMemo(() => {
    const emDia = cards.filter((c) => c.status === "em_dia").length;
    const precisamAtencao = cards
      .filter((c) => c.status !== "em_dia")
      // Crítico antes de atenção: a fila é por urgência, não por nome.
      .sort((a, b) => (a.status === "critico" ? -1 : 1) - (b.status === "critico" ? -1 : 1));

    const comTaxa = cards.filter((c) => c.correct_rate !== null);
    const taxaMedia = comTaxa.length
      ? Math.round((comTaxa.reduce((s, c) => s + (c.correct_rate ?? 0), 0) / comTaxa.length) * 100)
      : null;

    // Quantos alunos travam em cada tópico — é o que diz o que retomar na aula.
    const contagem = new Map<string, number>();
    for (const c of cards) {
      for (const t of c.struggling_topics) contagem.set(t, (contagem.get(t) ?? 0) + 1);
    }
    const topicosCriticos = [...contagem.entries()]
      .sort((a, b) => b[1] - a[1])
      .slice(0, 5);

    return {
      emDia,
      precisamAtencao,
      taxaMedia,
      topicosCriticos,
      exercicios: cards.reduce((s, c) => s + c.exercises_attempted, 0),
      sessoes: cards.reduce((s, c) => s + c.sessions_count, 0),
    };
  }, [cards]);

  return (
    <div className="mx-auto w-full max-w-6xl px-4 pb-16 pt-8">
      <Reveal>
        <PageHead
          titulo={
            <>
              Painel da <span className="text-gradient">turma</span>
            </>
          }
          descricao="Como seus alunos estão usando o NERV: quem está em dia, quem precisa de você e onde a turma trava."
          acao={
            <Link
              href="/alunos"
              className="focus-nice inline-flex items-center gap-1.5 rounded-full border border-border px-4 py-2.5 text-sm font-medium text-muted-foreground transition-colors duration-300 hover:border-primary/40 hover:text-foreground"
            >
              Ver todos os alunos
              <ArrowUpRight className="size-4" />
            </Link>
          }
        />
      </Reveal>

      {error && (
        <p className="mt-6 text-sm text-destructive" role="alert">
          {error}
        </p>
      )}

      {carregando ? (
        <p className="shimmer-text mt-8 text-sm font-medium">Carregando sua turma</p>
      ) : cards.length === 0 && !error ? (
        <Panel className="mt-7">
          <p className="text-sm leading-relaxed text-muted-foreground">
            Nenhum aluno cadastrado ainda. Assim que os alunos entrarem na plataforma, os números
            aparecem aqui.
          </p>
        </Panel>
      ) : (
        <>
          <div className="mt-7 grid grid-cols-2 gap-3 sm:gap-4 lg:grid-cols-4">
            {[
              {
                label: "Alunos em dia",
                value: `${resumo.emDia}/${cards.length}`,
                icon: Users,
                hint: "sem sinal de abandono",
                tone: "primary" as const,
              },
              {
                label: "Precisam de atenção",
                value: resumo.precisamAtencao.length,
                icon: AlertTriangle,
                hint: "atenção ou crítico",
                tone: "streak" as const,
              },
              {
                label: "Taxa de acerto",
                value: resumo.taxaMedia === null ? "—" : `${resumo.taxaMedia}%`,
                icon: Target,
                hint:
                  resumo.taxaMedia === null
                    ? "ninguém respondeu exercícios ainda"
                    : "média da turma",
                tone: "badge" as const,
              },
              {
                label: "Sessões de tutoria",
                value: resumo.sessoes,
                icon: MessageCircle,
                hint: `${resumo.exercicios} exercícios respondidos`,
                tone: "muted" as const,
              },
            ].map((m, i) => (
              <Reveal key={m.label} delay={0.06 * i}>
                <Metric {...m} />
              </Reveal>
            ))}
          </div>

          <div className="mt-4 grid gap-4 lg:grid-cols-[1.3fr_1fr]">
            <Reveal delay={0.24}>
              <Panel
                titulo="Quem precisa de você agora"
                acao={
                  <Link
                    href="/alunos"
                    className="focus-nice text-sm font-semibold text-primary hover:opacity-80"
                  >
                    ver todos
                  </Link>
                }
              >
                {resumo.precisamAtencao.length === 0 ? (
                  <p className="text-sm leading-relaxed text-muted-foreground">
                    Ninguém em situação de atenção. Turma inteira em dia — aproveite para puxar o
                    nível.
                  </p>
                ) : (
                  <ul className="space-y-2">
                    {resumo.precisamAtencao.slice(0, 6).map((c) => (
                      <li
                        key={c.student_id}
                        className="flex items-start justify-between gap-3 rounded-2xl bg-surface-2/50 px-4 py-3"
                      >
                        <div className="min-w-0">
                          <p className="truncate text-sm font-medium">{c.name}</p>
                          <p className="text-xs text-muted-foreground">
                            {c.grade ?? "série não informada"} ·{" "}
                            {c.correct_rate !== null
                              ? `${Math.round(c.correct_rate * 100)}% de acerto`
                              : "sem exercícios"}
                          </p>
                          {c.struggling_topics.length > 0 && (
                            <div className="mt-2 flex flex-wrap gap-1.5">
                              {c.struggling_topics.slice(0, 3).map((t) => (
                                <Tag key={t}>{t}</Tag>
                              ))}
                            </div>
                          )}
                        </div>
                        <StatusPill status={c.status} />
                      </li>
                    ))}
                  </ul>
                )}
              </Panel>
            </Reveal>

            <Reveal delay={0.3}>
              <Panel titulo="Onde a turma trava">
                {resumo.topicosCriticos.length === 0 ? (
                  <p className="text-sm leading-relaxed text-muted-foreground">
                    Ainda não há tópicos com dificuldade registrada. Eles aparecem conforme os
                    alunos respondem exercícios.
                  </p>
                ) : (
                  <div className="space-y-4">
                    {resumo.topicosCriticos.map(([topico, quantos]) => (
                      <Bar
                        key={topico}
                        label={topico}
                        pct={Math.round((quantos / cards.length) * 100)}
                        right={`${quantos} ${quantos === 1 ? "aluno" : "alunos"}`}
                      />
                    ))}
                    <p className="flex items-start gap-2 pt-1 text-xs leading-relaxed text-muted-foreground">
                      <ListChecks className="mt-0.5 size-3.5 shrink-0 text-primary" />
                      Proporção de alunos da turma com dificuldade registrada em cada tópico.
                    </p>
                  </div>
                )}
              </Panel>
            </Reveal>
          </div>
        </>
      )}
    </div>
  );
}
