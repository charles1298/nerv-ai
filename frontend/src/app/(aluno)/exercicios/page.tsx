"use client";

// Feed de exercícios adaptativos com feedback imediato (seção 7.1).

import { useEffect, useRef, useState } from "react";
import {
  api,
  ApiError,
  type AttemptResult,
  type ExercisePublic,
  type SubjectPublic,
  type TopicPublic,
} from "@/lib/api";
import { MathRenderer } from "@/components/chat/MathRenderer";

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
    api.listSubjects().then(setSubjects).catch(() => setError("Falha ao carregar matérias."));
  }, []);

  useEffect(() => {
    if (!selectedSubject) return;
    setTopics([]);
    setSelectedTopic("");
    api.listTopics(selectedSubject).then(setTopics).catch(() => setError("Falha ao carregar tópicos."));
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
    <div className="mx-auto max-w-3xl space-y-6 p-6">
      <h1 className="font-display text-2xl font-bold">Exercícios</h1>

      <div className="flex flex-wrap gap-3">
        <select
          value={selectedSubject}
          onChange={(e) => setSelectedSubject(e.target.value)}
          className="rounded-lg border border-nerv-border bg-nerv-surface px-3 py-2 text-sm"
        >
          <option value="">Matéria...</option>
          {subjects.map((s) => (
            <option key={s.id} value={s.id}>
              {s.name}
            </option>
          ))}
        </select>
        <select
          value={selectedTopic}
          onChange={(e) => setSelectedTopic(e.target.value)}
          disabled={!topics.length}
          className="rounded-lg border border-nerv-border bg-nerv-surface px-3 py-2 text-sm disabled:opacity-50"
        >
          <option value="">Tópico...</option>
          {topics.map((t) => (
            <option key={t.id} value={t.id}>
              {t.name}
            </option>
          ))}
        </select>
        <button
          onClick={() => void generate()}
          disabled={!selectedTopic || loading}
          className="rounded-lg bg-nerv-purple px-4 py-2 font-display text-sm font-medium transition hover:bg-nerv-purple-dim disabled:opacity-50"
        >
          {loading && !exercise ? "Gerando..." : "Gerar exercício"}
        </button>
      </div>

      {error && <p className="text-sm text-red-400">{error}</p>}

      {exercise && (
        <div className="rounded-2xl border border-nerv-border bg-nerv-surface p-6">
          <div className="mb-3 flex items-center gap-2 text-xs text-nerv-muted">
            <span className="rounded bg-nerv-purple/20 px-2 py-0.5 text-nerv-purple">
              Nível {exercise.difficulty}/5
            </span>
          </div>
          <div className="text-sm leading-relaxed">
            <MathRenderer content={exercise.question} />
          </div>

          <div className="mt-4 space-y-2">
            {exercise.alternatives.map((alt) => (
              <button
                key={alt.label}
                onClick={() => !result && setSelectedAnswer(alt.label)}
                disabled={!!result}
                className={`block w-full rounded-lg border px-4 py-3 text-left text-sm transition ${
                  selectedAnswer === alt.label
                    ? "border-nerv-purple bg-nerv-purple/10"
                    : "border-nerv-border hover:border-nerv-muted"
                }`}
              >
                <span className="mr-2 font-display font-bold text-nerv-purple">{alt.label})</span>
                <MathRenderer content={alt.text} />
              </button>
            ))}
          </div>

          {!result && (
            <button
              onClick={() => void submit()}
              disabled={!selectedAnswer || loading}
              className="mt-4 rounded-lg bg-nerv-neon/90 px-4 py-2 font-display text-sm font-bold text-nerv-bg transition hover:bg-nerv-neon disabled:opacity-50"
            >
              {loading ? "Corrigindo..." : "Responder"}
            </button>
          )}

          {result && (
            <div
              className={`mt-4 rounded-xl border p-4 text-sm ${
                result.is_correct
                  ? "border-nerv-neon/40 bg-nerv-neon/5"
                  : "border-red-500/40 bg-red-500/5"
              }`}
            >
              <p className="font-display font-bold">
                {result.is_correct ? "✓ Acertou! +30 XP" : "✗ Não foi dessa vez"}
              </p>
              <p className="mt-2 text-nerv-muted">{result.feedback}</p>
              <details className="mt-3">
                <summary className="cursor-pointer text-nerv-purple">
                  Ver resolução passo a passo
                </summary>
                <div className="mt-2 leading-relaxed">
                  <MathRenderer content={result.step_by_step_solution} />
                </div>
              </details>
              <button
                onClick={() => void generate()}
                className="mt-4 rounded-lg bg-nerv-purple px-4 py-2 font-display text-xs font-medium"
              >
                Próximo exercício →
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
