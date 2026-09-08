"use client";

// Cronograma de estudos personalizado (seções 5.6 e 7.1).
//
// A tela tem duas fases: o formulário, que coleta a restrição real do aluno
// (quantos dias, quantos minutos), e o plano, que mostra semana a semana o que
// fazer. O histórico embaixo permite voltar a um plano anterior.

import { useEffect, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import {
  BookOpen,
  CalendarDays,
  Clock,
  Coffee,
  ListChecks,
  PenLine,
  PlayCircle,
  RotateCcw,
  Sparkles,
  Timer,
  Trash2,
  type LucideIcon,
} from "lucide-react";
import {
  api,
  ApiError,
  type AtividadeCronograma,
  type CronogramaPublic,
  type CronogramaResumo,
  type SubjectPublic,
} from "@/lib/api";
import { MathRenderer } from "@/components/chat/MathRenderer";
import { Reveal } from "@/components/nerv/Reveal";

const OPCOES_SEMANAS = [1, 2, 4, 6, 8, 12];
const OPCOES_DIAS = [2, 3, 4, 5, 6, 7];
const OPCOES_MINUTOS = [15, 30, 45, 60, 90, 120];

// Cada atividade tem ícone e cor próprios. É o que deixa a semana legível de
// relance — o aluno bate o olho e vê que quarta é dia de simulado.
const ESTILO_ATIVIDADE: Record<
  AtividadeCronograma,
  { icone: LucideIcon; rotulo: string; cor: string }
> = {
  revisao: { icone: RotateCcw, rotulo: "Revisão", cor: "text-badge" },
  exercicios: { icone: ListChecks, rotulo: "Exercícios", cor: "text-primary" },
  leitura: { icone: BookOpen, rotulo: "Leitura", cor: "text-xp" },
  redacao: { icone: PenLine, rotulo: "Redação", cor: "text-streak" },
  simulado: { icone: Timer, rotulo: "Simulado", cor: "text-destructive" },
  videoaula: { icone: PlayCircle, rotulo: "Videoaula", cor: "text-badge" },
  descanso: { icone: Coffee, rotulo: "Descanso", cor: "text-muted-foreground" },
};

function estiloDe(atividade: AtividadeCronograma) {
  return ESTILO_ATIVIDADE[atividade] ?? ESTILO_ATIVIDADE.exercicios;
}

function formataData(iso: string) {
  return new Date(iso).toLocaleDateString("pt-BR", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}

export default function CronogramaPage() {
  const [objetivo, setObjetivo] = useState("");
  const [semanas, setSemanas] = useState(4);
  const [diasPorSemana, setDiasPorSemana] = useState(3);
  const [minutosPorDia, setMinutosPorDia] = useState(45);
  const [materias, setMaterias] = useState<string[]>([]);

  const [subjects, setSubjects] = useState<SubjectPublic[]>([]);
  const [plano, setPlano] = useState<CronogramaPublic | null>(null);
  const [historico, setHistorico] = useState<CronogramaResumo[]>([]);
  const [semanaAberta, setSemanaAberta] = useState(1);

  const [gerando, setGerando] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .listSubjects()
      .then(setSubjects)
      .catch(() => undefined);
    api
      .listCronogramas()
      .then(setHistorico)
      .catch(() => undefined);
  }, []);

  const alternaMateria = (nome: string) =>
    setMaterias((atual) =>
      atual.includes(nome) ? atual.filter((m) => m !== nome) : [...atual, nome],
    );

  const gerar = async () => {
    if (objetivo.trim().length < 5 || gerando) return;
    setGerando(true);
    setError(null);
    try {
      const novo = await api.createCronograma({
        objetivo: objetivo.trim(),
        semanas,
        dias_por_semana: diasPorSemana,
        minutos_por_dia: minutosPorDia,
        materias,
      });
      setPlano(novo);
      setSemanaAberta(1);
      setHistorico((prev) => [
        {
          id: novo.id,
          objetivo: novo.objetivo,
          semanas_total: novo.semanas_total,
          dias_por_semana: novo.dias_por_semana,
          minutos_por_dia: novo.minutos_por_dia,
          created_at: novo.created_at,
        },
        ...prev,
      ]);
    } catch (e) {
      setError(
        e instanceof ApiError ? e.message : "Não consegui montar seu cronograma. Tente de novo.",
      );
    } finally {
      setGerando(false);
    }
  };

  const abrir = async (id: string) => {
    setError(null);
    try {
      setPlano(await api.getCronograma(id));
      setSemanaAberta(1);
    } catch {
      setError("Não consegui abrir esse cronograma.");
    }
  };

  const excluir = async (id: string) => {
    setError(null);
    try {
      await api.deleteCronograma(id);
      setHistorico((prev) => prev.filter((c) => c.id !== id));
      if (plano?.id === id) setPlano(null);
    } catch {
      setError("Não consegui excluir esse cronograma.");
    }
  };

  return (
    <div className="mx-auto w-full max-w-5xl px-4 pb-28 pt-8 md:pb-12">
      <Reveal>
        <h1 className="font-display text-3xl font-bold sm:text-4xl">
          Seu <span className="text-gradient">cronograma</span> de estudos
        </h1>
        <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
          Me diga quanto tempo você tem de verdade. Monto um plano que cabe na sua rotina e começa
          pelo que você mais precisa destravar.
        </p>
      </Reveal>

      {/* ---------- formulário ---------- */}
      <Reveal delay={0.08}>
        <div className="surface-card mt-6 p-5 sm:p-7">
          <label htmlFor="objetivo" className="text-sm font-medium">
            Qual é o seu objetivo?
          </label>
          <input
            id="objetivo"
            value={objetivo}
            onChange={(e) => setObjetivo(e.target.value)}
            placeholder="Ex.: passar na prova de matemática do bimestre"
            className="mt-2 w-full rounded-xl border border-border bg-surface-2/60 px-4 py-3 text-sm outline-none transition-colors duration-300 placeholder:text-muted-foreground focus:border-primary/60"
          />

          <div className="mt-6 grid gap-6 sm:grid-cols-3">
            <Seletor
              titulo="Por quantas semanas?"
              icone={CalendarDays}
              opcoes={OPCOES_SEMANAS}
              valor={semanas}
              onChange={setSemanas}
              sufixo={(v) => (v === 1 ? "semana" : "semanas")}
            />
            <Seletor
              titulo="Dias por semana"
              icone={CalendarDays}
              opcoes={OPCOES_DIAS}
              valor={diasPorSemana}
              onChange={setDiasPorSemana}
              sufixo={() => "dias"}
            />
            <Seletor
              titulo="Minutos por dia"
              icone={Clock}
              opcoes={OPCOES_MINUTOS}
              valor={minutosPorDia}
              onChange={setMinutosPorDia}
              sufixo={() => "min"}
            />
          </div>

          {subjects.length > 0 && (
            <div className="mt-6">
              <p className="text-sm font-medium">
                Priorizar alguma matéria?{" "}
                <span className="text-muted-foreground">(opcional)</span>
              </p>
              <div className="mt-3 flex flex-wrap gap-2">
                {subjects.map((s) => (
                  <button
                    key={s.id}
                    type="button"
                    onClick={() => alternaMateria(s.name)}
                    className={`focus-nice rounded-full border px-3.5 py-2 text-sm transition-colors duration-300 ${
                      materias.includes(s.name)
                        ? "border-primary bg-primary/15 text-foreground"
                        : "border-border bg-surface/60 text-muted-foreground hover:border-primary/40 hover:text-foreground"
                    }`}
                  >
                    {s.name}
                  </button>
                ))}
              </div>
            </div>
          )}

          <motion.button
            type="button"
            onClick={() => void gerar()}
            disabled={objetivo.trim().length < 5 || gerando}
            whileTap={{ scale: 0.97 }}
            className="focus-nice mt-7 inline-flex items-center gap-2 rounded-full bg-primary px-5 py-3 text-sm font-semibold text-primary-foreground transition-opacity duration-300 disabled:opacity-40"
          >
            <Sparkles className="size-4" />
            {gerando ? "Montando seu cronograma..." : "Gerar meu cronograma"}
          </motion.button>

          {gerando && (
            <p className="shimmer-text mt-3 text-sm font-medium">
              Cruzando seu histórico com o tempo que você tem
            </p>
          )}

          {error && (
            <p className="mt-3 text-sm text-destructive" role="alert">
              {error}
            </p>
          )}
        </div>
      </Reveal>

      {/* ---------- plano gerado ---------- */}
      <AnimatePresence>
        {plano && (
          <motion.div
            key={plano.id}
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
            className="mt-6 space-y-4"
          >
            <div className="surface-card glow-ring p-5 sm:p-7">
              <p className="text-xs uppercase tracking-wide text-primary">Seu plano</p>
              <h2 className="mt-2 font-display text-xl font-bold">{plano.objetivo}</h2>
              <p className="mt-3 text-sm leading-relaxed text-muted-foreground">
                <MathRenderer content={plano.resumo} />
              </p>

              <div className="mt-5 flex flex-wrap gap-2 text-xs">
                <Etiqueta icone={CalendarDays}>
                  {plano.semanas_total} {plano.semanas_total === 1 ? "semana" : "semanas"}
                </Etiqueta>
                <Etiqueta icone={CalendarDays}>{plano.dias_por_semana} dias por semana</Etiqueta>
                <Etiqueta icone={Clock}>{plano.minutos_por_dia} min por dia</Etiqueta>
              </div>

              <div className="mt-5 rounded-2xl bg-surface-2/50 p-4">
                <p className="text-sm font-semibold">Por que montei assim</p>
                <p className="mt-1.5 text-sm leading-relaxed text-muted-foreground">
                  <MathRenderer content={plano.estrategia} />
                </p>
              </div>
            </div>

            {plano.semanas.map((semana) => {
              const aberta = semanaAberta === semana.numero;
              return (
                <div key={semana.numero} className="surface-card overflow-hidden">
                  <button
                    type="button"
                    onClick={() => setSemanaAberta(aberta ? -1 : semana.numero)}
                    className="focus-nice flex w-full items-center justify-between gap-4 p-5 text-left"
                  >
                    <span className="min-w-0">
                      <span className="text-xs uppercase tracking-wide text-primary">
                        Semana {semana.numero}
                      </span>
                      <span className="mt-1 block font-semibold">
                        <MathRenderer content={semana.foco} />
                      </span>
                    </span>
                    <span className="shrink-0 text-xs text-muted-foreground">
                      {aberta ? "ocultar" : "ver dias"}
                    </span>
                  </button>

                  {aberta && (
                    <div className="grid gap-3 border-t border-border p-5 sm:grid-cols-2">
                      {semana.dias.map((dia) => {
                        const total = dia.blocos.reduce((s, b) => s + b.minutos, 0);
                        return (
                          <div key={dia.dia} className="rounded-2xl bg-surface-2/50 p-4">
                            <div className="flex items-baseline justify-between gap-2">
                              <p className="font-display font-bold">{dia.dia}</p>
                              <p className="text-xs text-muted-foreground">{total} min</p>
                            </div>
                            <ul className="mt-3 space-y-3">
                              {dia.blocos.map((bloco, i) => {
                                const { icone: Icone, rotulo, cor } = estiloDe(bloco.atividade);
                                return (
                                  <li key={i} className="flex gap-3">
                                    <span
                                      className={`mt-0.5 grid size-8 shrink-0 place-items-center rounded-lg bg-background/60 ring-1 ring-border ${cor}`}
                                    >
                                      <Icone className="size-4" />
                                    </span>
                                    <span className="min-w-0">
                                      <span className="block text-sm font-medium">
                                        {bloco.materia} · {bloco.topico}
                                      </span>
                                      <span className="block text-xs text-muted-foreground">
                                        {rotulo} · {bloco.minutos} min
                                      </span>
                                      <span className="mt-1 block text-sm leading-relaxed text-muted-foreground">
                                        <MathRenderer content={bloco.descricao} />
                                      </span>
                                    </span>
                                  </li>
                                );
                              })}
                            </ul>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              );
            })}

            {plano.dicas.length > 0 && (
              <div className="surface-card p-5 sm:p-6">
                <h3 className="flex items-center gap-2 font-display font-bold">
                  <Sparkles className="size-4 text-badge" /> Dicas para não largar no meio
                </h3>
                <ul className="mt-3 space-y-2">
                  {plano.dicas.map((dica, i) => (
                    <li key={i} className="text-sm leading-relaxed text-muted-foreground">
                      <MathRenderer content={dica} />
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>

      {/* ---------- histórico ---------- */}
      {historico.length > 0 && (
        <Reveal delay={0.16}>
          <div className="surface-card mt-6 p-5 sm:p-6">
            <h3 className="font-display font-bold">Seus cronogramas</h3>
            <ul className="mt-3 space-y-2">
              {historico.map((c) => (
                <li
                  key={c.id}
                  className="flex items-center justify-between gap-3 rounded-2xl bg-surface-2/50 px-4 py-3"
                >
                  <button
                    type="button"
                    onClick={() => void abrir(c.id)}
                    className="focus-nice min-w-0 flex-1 text-left"
                  >
                    <span className="block truncate text-sm font-medium">{c.objetivo}</span>
                    <span className="block text-xs text-muted-foreground">
                      {c.semanas_total} {c.semanas_total === 1 ? "semana" : "semanas"} ·{" "}
                      {c.minutos_por_dia} min/dia · {formataData(c.created_at)}
                    </span>
                  </button>
                  <button
                    type="button"
                    onClick={() => void excluir(c.id)}
                    aria-label={"Excluir cronograma: " + c.objetivo}
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

function Seletor({
  titulo,
  icone: Icone,
  opcoes,
  valor,
  onChange,
  sufixo,
}: {
  titulo: string;
  icone: LucideIcon;
  opcoes: number[];
  valor: number;
  onChange: (v: number) => void;
  sufixo: (v: number) => string;
}) {
  return (
    <div>
      <p className="flex items-center gap-1.5 text-sm font-medium">
        <Icone className="size-4 text-primary" />
        {titulo}
      </p>
      <div className="mt-2 flex flex-wrap gap-2">
        {opcoes.map((o) => (
          <button
            key={o}
            type="button"
            onClick={() => onChange(o)}
            className={`focus-nice rounded-xl border px-3 py-1.5 text-sm transition-colors duration-300 ${
              valor === o
                ? "border-primary bg-primary/15 text-foreground"
                : "border-border bg-surface/60 text-muted-foreground hover:border-primary/40 hover:text-foreground"
            }`}
          >
            {o} <span className="text-xs">{sufixo(o)}</span>
          </button>
        ))}
      </div>
    </div>
  );
}

function Etiqueta({ icone: Icone, children }: { icone: LucideIcon; children: React.ReactNode }) {
  return (
    <span className="inline-flex items-center gap-1.5 rounded-full border border-border bg-surface/60 px-3 py-1.5 text-muted-foreground">
      <Icone className="size-3.5 text-primary" />
      {children}
    </span>
  );
}
