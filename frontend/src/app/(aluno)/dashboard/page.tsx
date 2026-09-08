"use client";

// Home do aluno: streak, XP, badges e atalhos (seção 7.1).
//
// Visual portado do pacote "AI Tutor Studio". O cartão de meta semanal, que no
// protótipo tinha 72% fixo, aqui mede a sequência real de dias estudados sobre
// os 7 da semana — é o único progresso semanal que a API realmente conhece.

import { useEffect, useState } from "react";
import { Flame, ListChecks, Medal, MessageCircle, PenLine, Sparkles, Zap } from "lucide-react";
import { api, type EssayPublic, type GamificationState } from "@/lib/api";
import { useAuthStore } from "@/store/auth";
import { Reveal } from "@/components/nerv/Reveal";
import { ActionCard, ProgressBar, StatCard } from "@/components/nerv/Cards";

const DIAS_NA_SEMANA = 7;
const NOTA_MAXIMA_REDACAO = 1000;

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
  const primeiroNome = user?.name?.split(" ")[0] ?? "estudante";
  const diasSeguidos = Math.min(gam?.streak_days ?? 0, DIAS_NA_SEMANA);
  const progressoSemana = Math.round((diasSeguidos / DIAS_NA_SEMANA) * 100);
  const faltamDias = DIAS_NA_SEMANA - diasSeguidos;

  const stats = [
    { label: "XP total", value: gam?.xp_total ?? 0, icon: Zap, tone: "primary" as const },
    {
      label: "Ofensiva",
      value: gam?.streak_days ?? 0,
      suffix: "dias",
      icon: Flame,
      tone: "streak" as const,
    },
    { label: "Conquistas", value: gam?.badges.length ?? 0, icon: Medal, tone: "badge" as const },
    {
      label: "Última redação",
      value: lastEssay?.nota_total ?? "—",
      suffix: lastEssay?.nota_total ? "/1000" : undefined,
      icon: PenLine,
      tone: "muted" as const,
    },
  ];

  const atalhos = [
    {
      href: "/chat",
      title: "Tutoria",
      description: "Converse com o NERV e tire qualquer dúvida na hora, do seu jeito.",
      icon: MessageCircle,
      cta: "Começar conversa",
    },
    {
      href: "/exercicios",
      title: "Exercícios",
      description: "Pratique no seu nível e ganhe XP a cada acerto, com feedback na hora.",
      icon: ListChecks,
      cta: "Praticar agora",
    },
    {
      href: "/redacao",
      title: "Redação",
      description: "Envie seu texto e receba correção completa em poucos minutos.",
      icon: PenLine,
      cta: "Enviar redação",
    },
  ];

  return (
    <div className="mx-auto w-full max-w-6xl px-4 pb-28 pt-8 md:pb-12">
      <Reveal>
        <p className="text-sm text-muted-foreground">Bem-vindo de volta</p>
        <h1 className="mt-1 font-display text-3xl font-bold sm:text-4xl">
          Olá, {primeiroNome}! <span className="text-gradient">Vamos estudar?</span>
        </h1>
      </Reveal>

      {error && (
        <p className="mt-4 text-sm text-destructive" role="alert">
          {error}
        </p>
      )}

      <div className="mt-7 grid grid-cols-2 gap-3 sm:gap-4 lg:grid-cols-4">
        {stats.map((s, i) => (
          <Reveal key={s.label} delay={0.06 * i}>
            <StatCard {...s} />
          </Reveal>
        ))}
      </div>

      <Reveal delay={0.18} className="mt-4">
        <div className="surface-card p-5 sm:p-6">
          <h2 className="text-base font-semibold">Sua semana</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            {faltamDias === 0
              ? "Semana completa, sete dias seguidos. Impressionante!"
              : `Faltam ${faltamDias} ${faltamDias === 1 ? "dia" : "dias"} para fechar a semana. Você consegue!`}
          </p>
          <div className="mt-4">
            <ProgressBar
              value={progressoSemana}
              label={`${diasSeguidos} de ${DIAS_NA_SEMANA} dias seguidos`}
            />
          </div>
        </div>
      </Reveal>

      {gam && gam.badges.length > 0 && (
        <Reveal delay={0.22} className="mt-4">
          <div className="surface-card p-5 sm:p-6">
            <h2 className="flex items-center gap-2 text-base font-semibold">
              <Sparkles className="size-4 text-badge" /> Conquistas
            </h2>
            <div className="mt-3 flex flex-wrap gap-2">
              {gam.badges.map((b) => (
                <span
                  key={b.id}
                  className="inline-flex items-center gap-1.5 rounded-full border border-border bg-primary/10 px-3 py-1 text-xs text-primary"
                >
                  <Medal className="size-3.5" />
                  {b.name}
                </span>
              ))}
            </div>
          </div>
        </Reveal>
      )}

      <h2 className="mt-10 text-lg font-semibold">O que você quer fazer agora?</h2>
      <div className="mt-4 grid gap-4 md:grid-cols-3">
        {atalhos.map((c, i) => (
          <Reveal key={c.href} delay={0.24 + i * 0.08}>
            <ActionCard {...c} />
          </Reveal>
        ))}
      </div>

      {essays.length > 0 && (
        <Reveal delay={0.48} className="mt-10">
          <div className="surface-card p-5 sm:p-6">
            <h2 className="text-base font-semibold">Evolução nas redações</h2>
            <div className="mt-4 flex items-end gap-2">
              {essays
                .slice(0, 10)
                .reverse()
                .map((e) => (
                  <div key={e.id} className="flex flex-1 flex-col items-center gap-1.5">
                    <div
                      className="w-full max-w-10 rounded-t-md bg-gradient-to-t from-primary/40 to-primary"
                      style={{
                        height: `${Math.max(((e.nota_total ?? 0) / NOTA_MAXIMA_REDACAO) * 96, 4)}px`,
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
