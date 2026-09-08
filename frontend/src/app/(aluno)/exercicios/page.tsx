"use client";

// Série de exercícios adaptativos com feedback imediato (seção 7.1).
//
// O fluxo é "tentar até acertar", não "acertou ou errou, próxima": ao errar, o
// aluno lê por que errou e escolhe de novo, com a alternativa já descartada
// fora de jogo. A resolução passo a passo só aparece depois do acerto — antes
// disso ela entregaria a resposta e mataria a tentativa.
//
// A série tem 5 questões, geradas uma a uma. Gerar as cinco de antemão custaria
// cinco chamadas ao modelo antes da primeira pergunta aparecer, e perderia a
// adaptação: o gerador usa o histórico do aluno, que muda a cada questão.

import { useEffect, useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import {
  BookOpen,
  Calculator,
  Check,
  FlaskConical,
  Globe2,
  RotateCcw,
  Sparkles,
  Trophy,
  X,
  type LucideIcon,
} from "lucide-react";
import {
  api,
  ApiError,
  type AttemptResult,
  type ExercisePublic,
  type SubjectPublic,
  type TopicPublic,
} from "@/lib/api";
import { MathRenderer } from "@/components/chat/MathRenderer";
import { Reveal } from "@/components/nerv/Reveal";
import { ProgressBar } from "@/components/nerv/Cards";

const TOTAL_QUESTOES = 5;

interface ResultadoQuestao {
  pergunta: string;
  tentativas: number;
}

function iconeDaMateria(nome: string): LucideIcon {
  const n = nome.toLowerCase();
  if (n.includes("matem")) return Calculator;
  if (n.includes("portugu") || n.includes("reda") || n.includes("liter")) return BookOpen;
  if (n.includes("cinc") || n.includes("ciên") || n.includes("bio") || n.includes("quím"))
    return FlaskConical;
  return Globe2;
}

export default function ExerciciosPage() {
  const [fase, setFase] = useState<"escolha" | "resolvendo" | "resumo">("escolha");

  const [subjects, setSubjects] = useState<SubjectPublic[]>([]);
  const [topics, setTopics] = useState<TopicPublic[]>([]);
  const [selectedSubject, setSelectedSubject] = useState("");
  const [selectedTopic, setSelectedTopic] = useState("");

  const [questao, setQuestao] = useState<ExercisePublic | null>(null);
  const [indice, setIndice] = useState(0);
  const [resultados, setResultados] = useState<ResultadoQuestao[]>([]);
  const [selecionada, setSelecionada] = useState("");
  const [erradas, setErradas] = useState<string[]>([]);
  const [tentativas, setTentativas] = useState(0);
  const [ultimo, setUltimo] = useState<AttemptResult | null>(null);
  const [acertou, setAcertou] = useState(false);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const startedAt = useRef<number>(Date.now());

  useEffect(() => {
    api
      .listSubjects()
      .then(setSubjects)
      .catch(() => setError("Falha ao carregar matérias."));
  }, []);

  useEffect(() => {
    if (!selectedSubject) return;
    setTopics([]);
    setSelectedTopic("");
    api
      .listTopics(selectedSubject)
      .then(setTopics)
      .catch(() => setError("Falha ao carregar tópicos."));
  }, [selectedSubject]);

  const gerarQuestao = async () => {
    if (!selectedTopic) return;
    setLoading(true);
    setError(null);
    setQuestao(null);
    setSelecionada("");
    setErradas([]);
    setTentativas(0);
    setUltimo(null);
    setAcertou(false);
    try {
      const ex = await api.generateExercise(selectedTopic);
      setQuestao(ex);
      startedAt.current = Date.now();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Falha ao gerar exercício.");
    } finally {
      setLoading(false);
    }
  };

  const iniciarSerie = async () => {
    setIndice(0);
    setResultados([]);
    setFase("resolvendo");
    await gerarQuestao();
  };

  const responder = async () => {
    if (!questao || !selecionada || loading || acertou) return;
    setLoading(true);
    setError(null);
    try {
      const gasto = Math.round((Date.now() - startedAt.current) / 1000);
      const res = await api.attemptExercise(questao.id, selecionada, gasto);
      const tentativaAtual = tentativas + 1;
      setTentativas(tentativaAtual);
      setUltimo(res);

      if (res.is_correct) {
        setAcertou(true);
        setResultados((prev) => [
          ...prev,
          { pergunta: questao.question, tentativas: tentativaAtual },
        ]);
      } else {
        // Tira a alternativa de circulação e devolve a escolha ao aluno.
        setErradas((prev) => [...prev, selecionada]);
        setSelecionada("");
      }
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Falha ao enviar resposta.");
    } finally {
      setLoading(false);
    }
  };

  const proxima = async () => {
    if (indice + 1 >= TOTAL_QUESTOES) {
      setFase("resumo");
      return;
    }
    setIndice((i) => i + 1);
    await gerarQuestao();
  };

  const acertosDePrimeira = resultados.filter((r) => r.tentativas === 1).length;

  // ---------- escolha de matéria e tópico ----------
  if (fase === "escolha") {
    return (
      <div className="mx-auto w-full max-w-5xl px-4 pb-28 pt-8 md:pb-12">
        <Reveal>
          <h1 className="font-display text-3xl font-bold sm:text-4xl">
            Escolha uma <span className="text-gradient">matéria</span>
          </h1>
          <p className="mt-2 text-sm text-muted-foreground">
            São {TOTAL_QUESTOES} questões. Errou? Sem problema: eu explico e você tenta de novo.
          </p>
        </Reveal>

        <div className="mt-6 grid grid-cols-2 gap-3 sm:gap-4 lg:grid-cols-4">
          {subjects.map((s, i) => {
            const Icone = iconeDaMateria(s.name);
            const ativa = selectedSubject === s.id;
            return (
              <Reveal key={s.id} delay={i * 0.06}>
                <motion.button
                  type="button"
                  onClick={() => setSelectedSubject(s.id)}
                  whileHover={{ y: -5 }}
                  whileTap={{ scale: 0.98 }}
                  transition={{ type: "spring", stiffness: 320, damping: 26 }}
                  className={`surface-card focus-nice w-full p-4 text-left sm:p-5 ${
                    ativa ? "glow-ring border-primary/50" : ""
                  }`}
                >
                  <span
                    className={`grid size-10 place-items-center rounded-xl ring-1 transition-colors duration-300 ${
                      ativa
                        ? "bg-primary text-primary-foreground ring-primary"
                        : "bg-primary/10 text-primary ring-primary/25"
                    }`}
                  >
                    <Icone className="size-5" />
                  </span>
                  <h2 className="mt-3 font-semibold">{s.name}</h2>
                  {s.bncc_code ? (
                    <p className="mt-1 text-xs text-muted-foreground">BNCC {s.bncc_code}</p>
                  ) : null}
                </motion.button>
              </Reveal>
            );
          })}
        </div>

        <AnimatePresence>
          {topics.length > 0 ? (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className="mt-8"
            >
              <p className="text-xs uppercase tracking-wide text-primary">Escolha o tópico</p>
              <div className="mt-3 flex flex-wrap gap-2">
                {topics.map((t) => (
                  <button
                    key={t.id}
                    type="button"
                    onClick={() => setSelectedTopic(t.id)}
                    className={`focus-nice rounded-full border px-3.5 py-2 text-sm transition-colors duration-300 ${
                      selectedTopic === t.id
                        ? "border-primary bg-primary/15 text-foreground"
                        : "border-border bg-surface/60 text-muted-foreground hover:border-primary/40 hover:text-foreground"
                    }`}
                  >
                    {t.name}
                  </button>
                ))}
              </div>
              <motion.button
                type="button"
                onClick={() => void iniciarSerie()}
                disabled={!selectedTopic || loading}
                whileTap={{ scale: 0.97 }}
                className="focus-nice mt-5 inline-flex items-center gap-2 rounded-full bg-primary px-5 py-3 text-sm font-semibold text-primary-foreground transition-opacity duration-300 disabled:opacity-40"
              >
                <Sparkles className="size-4" />
                {loading ? "Preparando..." : `Começar série de ${TOTAL_QUESTOES}`}
              </motion.button>
            </motion.div>
          ) : null}
        </AnimatePresence>

        {error && (
          <p className="mt-6 text-sm text-destructive" role="alert">
            {error}
          </p>
        )}
      </div>
    );
  }

  // ---------- resumo da série ----------
  if (fase === "resumo") {
    return (
      <div className="mx-auto w-full max-w-3xl px-4 pb-28 pt-8 md:pb-12">
        <Reveal>
          <div className="surface-card glow-ring p-6 sm:p-8">
            <span className="grid size-12 place-items-center rounded-2xl bg-primary/10 text-primary ring-1 ring-primary/25">
              <Trophy className="size-6" />
            </span>
            <h1 className="mt-4 font-display text-2xl font-bold sm:text-3xl">
              Série concluída, <span className="text-gradient">parabéns!</span>
            </h1>
            <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
              Você resolveu as {TOTAL_QUESTOES} questões — {acertosDePrimeira} de primeira. As
              outras você chegou lá tentando de novo, que é exatamente como se aprende.
            </p>

            <div className="mt-6">
              <ProgressBar
                value={Math.round((acertosDePrimeira / TOTAL_QUESTOES) * 100)}
                label={`${acertosDePrimeira} de ${TOTAL_QUESTOES} de primeira`}
              />
            </div>

            <ul className="mt-6 space-y-2">
              {resultados.map((r, i) => (
                <li
                  key={i}
                  className="flex items-start justify-between gap-4 rounded-2xl bg-surface-2/50 px-4 py-3 text-sm"
                >
                  <span className="min-w-0 flex-1 text-muted-foreground">
                    <span className="mr-2 font-display font-bold text-foreground">{i + 1}.</span>
                    <span className="line-clamp-2">{r.pergunta}</span>
                  </span>
                  <span
                    className={`shrink-0 rounded-full px-2.5 py-1 text-xs font-semibold ${
                      r.tentativas === 1
                        ? "bg-primary/15 text-primary"
                        : "bg-streak/15 text-streak"
                    }`}
                  >
                    {r.tentativas === 1 ? "de primeira" : `${r.tentativas} tentativas`}
                  </span>
                </li>
              ))}
            </ul>

            <div className="mt-7 flex flex-wrap gap-3">
              <motion.button
                type="button"
                onClick={() => void iniciarSerie()}
                whileTap={{ scale: 0.97 }}
                className="focus-nice inline-flex items-center gap-2 rounded-full bg-primary px-5 py-3 text-sm font-semibold text-primary-foreground transition-opacity duration-300"
              >
                <RotateCcw className="size-4" /> Outra série deste tópico
              </motion.button>
              <button
                type="button"
                onClick={() => setFase("escolha")}
                className="focus-nice inline-flex items-center gap-2 rounded-full border border-border px-5 py-3 text-sm font-medium text-muted-foreground transition-colors duration-300 hover:border-primary/40 hover:text-foreground"
              >
                Trocar de matéria
              </button>
            </div>
          </div>
        </Reveal>
      </div>
    );
  }

  // ---------- resolvendo ----------
  return (
    <div className="mx-auto w-full max-w-3xl px-4 pb-28 pt-8 md:pb-12">
      <Reveal>
        <div className="flex items-baseline justify-between">
          <p className="text-xs uppercase tracking-wide text-primary">
            Questão {indice + 1} de {TOTAL_QUESTOES}
          </p>
          {questao ? (
            <p className="text-xs text-muted-foreground">Nível {questao.difficulty} de 5</p>
          ) : null}
        </div>
        <div className="mt-3">
          <ProgressBar
            value={Math.round((indice / TOTAL_QUESTOES) * 100)}
            label="Progresso da série"
          />
        </div>
      </Reveal>

      {error && (
        <p className="mt-6 text-sm text-destructive" role="alert">
          {error}
        </p>
      )}

      {!questao && loading ? (
        <p className="shimmer-text mt-10 text-sm font-medium">Preparando sua questão</p>
      ) : null}

      {questao ? (
        <motion.div
          key={questao.id}
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
          className="surface-card mt-6 p-5 sm:p-7"
        >
          <h2 className="text-xl font-semibold">
            <MathRenderer content={questao.question} />
          </h2>

          <div className="mt-5 grid gap-3 sm:grid-cols-2">
            {questao.alternatives.map((alt) => {
              const jaErrada = erradas.includes(alt.label);
              const escolhida = selecionada === alt.label;
              const certa = acertou && escolhida;

              return (
                <motion.button
                  key={alt.label}
                  type="button"
                  onClick={() => !acertou && !jaErrada && setSelecionada(alt.label)}
                  disabled={acertou || jaErrada}
                  whileTap={acertou || jaErrada ? undefined : { scale: 0.97 }}
                  className={`focus-nice flex items-center justify-between gap-3 rounded-2xl border px-4 py-3.5 text-left text-base font-medium transition-colors duration-300 ${
                    certa
                      ? "border-primary bg-primary/15 text-foreground"
                      : jaErrada
                        ? "border-destructive/40 bg-destructive/5 text-muted-foreground line-through"
                        : escolhida
                          ? "border-primary/60 bg-primary/10 text-foreground"
                          : "border-border bg-surface/60 hover:border-primary/40"
                  }`}
                >
                  <span className="flex min-w-0 items-baseline gap-2">
                    <span className="font-display font-bold text-primary">{alt.label})</span>
                    <MathRenderer content={alt.text} />
                  </span>
                  {certa ? <Check className="size-5 shrink-0 text-primary" /> : null}
                  {jaErrada ? <X className="size-5 shrink-0 text-destructive" /> : null}
                </motion.button>
              );
            })}
          </div>

          {!acertou ? (
            <motion.button
              type="button"
              onClick={() => void responder()}
              disabled={!selecionada || loading}
              whileTap={{ scale: 0.97 }}
              className="focus-nice mt-5 inline-flex items-center gap-2 rounded-full bg-primary px-5 py-3 text-sm font-semibold text-primary-foreground transition-opacity duration-300 disabled:opacity-40"
            >
              {loading ? "Corrigindo..." : tentativas > 0 ? "Tentar de novo" : "Responder"}
            </motion.button>
          ) : null}

          <AnimatePresence>
            {ultimo ? (
              <motion.div
                key={`${tentativas}-${acertou}`}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                className="mt-6"
              >
                <p className="font-display text-lg font-bold">
                  {acertou ? (
                    <span className="text-primary">Isso! Você acertou.</span>
                  ) : (
                    <span className="text-foreground">Ainda não. Olha só por quê:</span>
                  )}
                </p>
                <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
                  {ultimo.feedback}
                </p>

                {!acertou ? (
                  <p className="mt-3 text-sm text-muted-foreground">
                    Descartei essa alternativa. Escolhe outra e tenta de novo — você consegue.
                  </p>
                ) : null}

                {/* A resolução só depois do acerto: antes, entregaria a resposta. */}
                {acertou ? (
                  <>
                    <details className="mt-4">
                      <summary className="focus-nice cursor-pointer list-none text-sm font-semibold text-primary">
                        Ver resolução passo a passo
                      </summary>
                      <div className="mt-3 rounded-2xl bg-surface-2/60 p-4 text-sm leading-relaxed">
                        <MathRenderer content={ultimo.step_by_step_solution} />
                      </div>
                    </details>

                    <motion.button
                      type="button"
                      onClick={() => void proxima()}
                      disabled={loading}
                      whileTap={{ scale: 0.97 }}
                      className="focus-nice mt-5 inline-flex items-center gap-2 rounded-full bg-primary px-5 py-3 text-sm font-semibold text-primary-foreground transition-opacity duration-300 disabled:opacity-40"
                    >
                      {indice + 1 >= TOTAL_QUESTOES ? "Ver meu resultado" : "Próxima questão"}
                    </motion.button>
                  </>
                ) : null}
              </motion.div>
            ) : null}
          </AnimatePresence>
        </motion.div>
      ) : null}
    </div>
  );
}
