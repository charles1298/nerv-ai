"use client";

// Feed de exercícios adaptativos com feedback imediato (seção 7.1).
//
// Visual portado do pacote "AI Tutor Studio". Uma diferença deliberada: lá cada
// matéria exibia uma barra de "12 de 20 atividades", número fixo no protótipo.
// A API não expõe progresso por matéria, então o cartão existe sem a barra —
// inventar o número daria ao aluno uma informação falsa sobre o próprio avanço.

import { useEffect, useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import {
  BookOpen,
  Calculator,
  Check,
  FlaskConical,
  Globe2,
  Sparkles,
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

function iconeDaMateria(nome: string): LucideIcon {
  const n = nome.toLowerCase();
  if (n.includes("matem")) return Calculator;
  if (n.includes("portugu") || n.includes("reda") || n.includes("liter")) return BookOpen;
  if (n.includes("cinc") || n.includes("ciên") || n.includes("bio") || n.includes("quím"))
    return FlaskConical;
  return Globe2;
}

export default function ExerciciosPage() {
  const [subjects, setSubjects] = useState<SubjectPublic[]>([]);
  const [topics, setTopics] = useState<TopicPublic[]>([]);
  const [selectedSubject, setSelectedSubject] = useState("");
  const [selectedTopic, setSelectedTopic] = useState("");
  const [exercise, setExercise] = useState<ExercisePublic | null>(null);
  const [result, setResult] = useState<AttemptResult | null>(null);
  const [selectedAnswer, setSelectedAnswer] = useState("");
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

  const generate = async () => {
    if (!selectedTopic) return;
    setLoading(true);
    setError(null);
    setResult(null);
    setSelectedAnswer("");
    try {
      const ex = await api.generateExercise(selectedTopic);
      setExercise(ex);
      startedAt.current = Date.now();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Falha ao gerar exercício.");
    } finally {
      setLoading(false);
    }
  };

  const submit = async () => {
    if (!exercise || !selectedAnswer) return;
    setLoading(true);
    setError(null);
    try {
      const elapsed = Math.round((Date.now() - startedAt.current) / 1000);
      const res = await api.attemptExercise(exercise.id, selectedAnswer, elapsed);
      setResult(res);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Falha ao enviar resposta.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mx-auto w-full max-w-5xl px-4 pb-28 pt-8 md:pb-12">
      <Reveal>
        <h1 className="font-display text-3xl font-bold sm:text-4xl">
          Escolha uma <span className="text-gradient">matéria</span>
        </h1>
        <p className="mt-2 text-sm text-muted-foreground">
          Um toque e a prática começa. Sem complicação.
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
              onClick={() => void generate()}
              disabled={!selectedTopic || loading}
              whileTap={{ scale: 0.97 }}
              className="focus-nice mt-5 inline-flex items-center gap-2 rounded-full bg-primary px-5 py-3 text-sm font-semibold text-primary-foreground transition-opacity duration-300 disabled:opacity-40"
            >
              <Sparkles className="size-4" />
              {loading && !exercise ? "Gerando..." : "Gerar exercício"}
            </motion.button>
          </motion.div>
        ) : null}
      </AnimatePresence>

      {error && (
        <p className="mt-6 text-sm text-destructive" role="alert">
          {error}
        </p>
      )}

      <AnimatePresence>
        {exercise ? (
          <motion.div
            key={exercise.id}
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
            className="surface-card mt-10 p-5 sm:p-7"
          >
            <p className="text-xs uppercase tracking-wide text-primary">
              Nível {exercise.difficulty} de 5
            </p>
            <h2 className="mt-2 text-xl font-semibold">
              <MathRenderer content={exercise.question} />
            </h2>

            <div className="mt-5 grid gap-3 sm:grid-cols-2">
              {exercise.alternatives.map((alt) => {
                const escolhida = selectedAnswer === alt.label;
                // A API devolve só se a alternativa escolhida estava certa, não
                // qual era a correta. Então marcamos apenas a escolha do aluno;
                // qual seria a resposta certa vem na resolução passo a passo.
                const estado = !result
                  ? escolhida
                    ? "escolhida"
                    : "neutra"
                  : escolhida
                    ? result.is_correct
                      ? "certa"
                      : "errada"
                    : "neutra";

                return (
                  <motion.button
                    key={alt.label}
                    type="button"
                    onClick={() => !result && setSelectedAnswer(alt.label)}
                    disabled={!!result}
                    whileTap={result ? undefined : { scale: 0.97 }}
                    className={`focus-nice flex items-center justify-between gap-3 rounded-2xl border px-4 py-3.5 text-left text-base font-medium transition-colors duration-300 ${
                      estado === "certa"
                        ? "border-primary bg-primary/15 text-foreground"
                        : estado === "errada"
                          ? "border-destructive bg-destructive/10 text-foreground"
                          : estado === "escolhida"
                            ? "border-primary/60 bg-primary/10 text-foreground"
                            : "border-border bg-surface/60 hover:border-primary/40"
                    }`}
                  >
                    <span className="flex min-w-0 items-baseline gap-2">
                      <span className="font-display font-bold text-primary">{alt.label})</span>
                      <MathRenderer content={alt.text} />
                    </span>
                    {estado === "certa" ? (
                      <Check className="size-5 shrink-0 text-primary" />
                    ) : null}
                    {estado === "errada" ? (
                      <X className="size-5 shrink-0 text-destructive" />
                    ) : null}
                  </motion.button>
                );
              })}
            </div>

            {!result ? (
              <motion.button
                type="button"
                onClick={() => void submit()}
                disabled={!selectedAnswer || loading}
                whileTap={{ scale: 0.97 }}
                className="focus-nice mt-5 inline-flex items-center gap-2 rounded-full bg-primary px-5 py-3 text-sm font-semibold text-primary-foreground transition-opacity duration-300 disabled:opacity-40"
              >
                {loading ? "Corrigindo..." : "Responder"}
              </motion.button>
            ) : null}

            <AnimatePresence>
              {result ? (
                <motion.div
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0 }}
                  className="mt-6"
                >
                  <p className="font-display text-lg font-bold">
                    {result.is_correct ? (
                      <span className="text-primary">Isso! Você acertou.</span>
                    ) : (
                      <span className="text-foreground">Quase! Vamos entender juntos.</span>
                    )}
                  </p>
                  <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
                    {result.feedback}
                  </p>

                  <details className="group mt-4">
                    <summary className="focus-nice cursor-pointer list-none text-sm font-semibold text-primary">
                      Ver resolução passo a passo
                    </summary>
                    <div className="mt-3 rounded-2xl bg-surface-2/60 p-4 text-sm leading-relaxed">
                      <MathRenderer content={result.step_by_step_solution} />
                    </div>
                  </details>

                  <motion.button
                    type="button"
                    onClick={() => void generate()}
                    whileTap={{ scale: 0.97 }}
                    className="focus-nice mt-5 inline-flex items-center gap-2 rounded-full border border-border px-5 py-3 text-sm font-medium text-muted-foreground transition-colors duration-300 hover:border-primary/40 hover:text-foreground"
                  >
                    Próximo exercício
                  </motion.button>
                </motion.div>
              ) : null}
            </AnimatePresence>
          </motion.div>
        ) : null}
      </AnimatePresence>
    </div>
  );
}
