"use client";

// Home do aluno: streak, XP, badges e atalhos (seção 7.1).

import { useEffect, useState } from "react";
import { Award, Flame, ListChecks, MessageCircle, PenLine, Sparkles, Zap } from "lucide-react";
import { api, type EssayPublic, type GamificationState } from "@/lib/api";
import { useAuthStore } from "@/store/auth";
import { Reveal } from "@/components/nerv/Reveal";
import { ActionCard, StatCard } from "@/components/nerv/Cards";

export default function DashboardPage() {
  const user = useAuthStore((s) => s.user);
  const [gam, setGam] = useState<GamificationState | null>(null);
  const [essays, setEssays] = useState<EssayPublic[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .myGamification()
      .then(setGam)
      .catch(() => setError("Falha ao carregar progresso."));
    api
      .listEssays()
      .then(setEssays)
      .catch(() => undefined);
  }, []);

  const lastEssay = essays[0];
  const notaMaxima = 1000;

  return (
    <div className="mx-auto w-full max-w-5xl space-y-8 px-4 pb-28 pt-8 md:pb-10">
      <Reveal>
        <h1 className="font-display text-2xl font-bold sm:text-3xl">
          Olá, {user?.name?.split(" ")[0] ?? "estudante"}! Bora estudar?
        </h1>
        <p className="mt-1.5 text-sm text-muted-foreground">
          Seu progresso de hoje, e por onde continuar.
        </p>
      </Reveal>

      {error && (
        <p className="text-sm text-destructive" role="alert">
          {error}
        </p>
      )}

      <Reveal delay={0.05}>
        <div className="grid grid-cols-2 gap-3 sm:gap-4 md:grid-cols-4">
          <StatCard label="XP total" value={gam?.xp_total ?? 0} icon={Zap} tone="primary" />
          <StatCard
            label="Sequência"
            value={gam?.streak_days ?? 0}
            suffix="dias"
            icon={Flame}
            tone="streak"
          />
          <StatCard label="Conquistas" value={gam?.badges.length ?? 0} icon={Award} tone="badge" />
          <StatCard
            label="Última redação"
            value={lastEssay?.nota_total ?? "—"}
            icon={PenLine}
            tone="muted"
          />
        </div>
      </Reveal>

      {gam && gam.badges.length > 0 && (
        <Reveal delay={0.1}>
          <div className="surface-card p-5">
            <h2 className="flex items-center gap-2 font-display font-bold">
              <Sparkles className="size-4 text-badge" /> Conquistas
            </h2>
            <div className="mt-3 flex flex-wrap gap-2">
              {gam.badges.map((b) => (
                <span
                  key={b.id}
                  className="inline-flex items-center gap-1.5 rounded-full border border-border bg-primary/10 px-3 py-1 text-xs text-primary"
                >
                  <Award className="size-3.5" />
                  {b.name}
                </span>
              ))}
            </div>
          </div>
        </Reveal>
      )}

      <Reveal delay={0.15}>
        <div className="grid gap-4 md:grid-cols-3">
          <ActionCard
            href="/chat"
            title="Tutoria"
            description="Tire dúvidas com o NERV agora, de qualquer matéria."
            icon={MessageCircle}
            cta="Conversar"
          />
          <ActionCard
            href="/exercicios"
            title="Exercícios"
            description="Pratique no seu nível, com feedback na hora."
            icon={ListChecks}
            cta="Praticar"
          />
          <ActionCard
            href="/redacao"
            title="Redação"
            description="Correção nos 5 critérios do ENEM em minutos."
            icon={PenLine}
            cta="Enviar redação"
          />
        </div>
      </Reveal>

      {essays.length > 0 && (
        <Reveal delay={0.2}>
          <div className="surface-card p-5">
            <h2 className="font-display font-bold">Evolução nas redações</h2>
            <div className="mt-4 flex items-end gap-2">
              {essays
                .slice(0, 10)
                .reverse()
                .map((e) => (
                  <div key={e.id} className="flex flex-1 flex-col items-center gap-1.5">
                    <div
                      className="w-full max-w-10 rounded-t-md bg-gradient-to-t from-primary/40 to-primary"
                      style={{
                        height: `${Math.max(((e.nota_total ?? 0) / notaMaxima) * 96, 4)}px`,
                      }}
                    />
                    <span className="text-[10px] text-muted-foreground">{e.nota_total}</span>
                  </div>
                ))}
            </div>
          </div>
        </Reveal>
      )}
    </div>
  );
}
