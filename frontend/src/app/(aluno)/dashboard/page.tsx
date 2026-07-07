"use client";

// Home do aluno: streak, XP, badges e atalhos (seção 7.1).

import Link from "next/link";
import { useEffect, useState } from "react";
import { api, type EssayPublic, type GamificationState } from "@/lib/api";
import { useAuthStore } from "@/store/auth";

export default function DashboardPage() {
  const user = useAuthStore((s) => s.user);
  const [gam, setGam] = useState<GamificationState | null>(null);
  const [essays, setEssays] = useState<EssayPublic[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.myGamification().then(setGam).catch(() => setError("Falha ao carregar progresso."));
    api.listEssays().then(setEssays).catch(() => undefined);
  }, []);

  const lastEssay = essays[0];

  return (
    <div className="mx-auto max-w-4xl space-y-6 p-6">
      <h1 className="font-display text-2xl font-bold">
        Olá, {user?.name?.split(" ")[0] ?? "estudante"}! 🚀
      </h1>
      {error && <p className="text-sm text-red-400">{error}</p>}

      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <div className="rounded-2xl border border-nerv-border bg-nerv-surface p-5">
          <p className="text-xs text-nerv-muted">XP total</p>
          <p className="mt-1 font-display text-3xl font-bold text-nerv-purple">
            {gam?.xp_total ?? 0}
          </p>
        </div>
        <div className="rounded-2xl border border-nerv-border bg-nerv-surface p-5">
          <p className="text-xs text-nerv-muted">Streak</p>
          <p className="mt-1 font-display text-3xl font-bold text-nerv-neon">
            {gam?.streak_days ?? 0} <span className="text-base">dias 🔥</span>
          </p>
        </div>
        <div className="rounded-2xl border border-nerv-border bg-nerv-surface p-5">
          <p className="text-xs text-nerv-muted">Badges</p>
          <p className="mt-1 font-display text-3xl font-bold">{gam?.badges.length ?? 0}</p>
        </div>
        <div className="rounded-2xl border border-nerv-border bg-nerv-surface p-5">
          <p className="text-xs text-nerv-muted">Última redação</p>
          <p className="mt-1 font-display text-3xl font-bold">
            {lastEssay?.nota_total ?? "—"}
          </p>
        </div>
      </div>

      {gam && gam.badges.length > 0 && (
        <div className="rounded-2xl border border-nerv-border bg-nerv-surface p-5">
          <h2 className="font-display font-bold">Conquistas</h2>
          <div className="mt-3 flex flex-wrap gap-2">
            {gam.badges.map((b) => (
              <span
                key={b.id}
                className="rounded-full border border-nerv-purple/50 bg-nerv-purple/10 px-3 py-1 text-xs text-nerv-purple"
              >
                🏅 {b.name}
              </span>
            ))}
          </div>
        </div>
      )}

      <div className="grid gap-4 md:grid-cols-3">
        <Link
          href="/chat"
          className="rounded-2xl border border-nerv-border bg-nerv-surface p-6 transition hover:border-nerv-purple"
        >
          <p className="font-display text-lg font-bold">💬 Tutoria</p>
          <p className="mt-1 text-sm text-nerv-muted">Tire dúvidas com o NERV agora.</p>
        </Link>
        <Link
          href="/exercicios"
          className="rounded-2xl border border-nerv-border bg-nerv-surface p-6 transition hover:border-nerv-purple"
        >
          <p className="font-display text-lg font-bold">📝 Exercícios</p>
          <p className="mt-1 text-sm text-nerv-muted">Pratique no seu nível, com feedback.</p>
        </Link>
        <Link
          href="/redacao"
          className="rounded-2xl border border-nerv-border bg-nerv-surface p-6 transition hover:border-nerv-purple"
        >
          <p className="font-display text-lg font-bold">✍️ Redação</p>
          <p className="mt-1 text-sm text-nerv-muted">Correção ENEM completa em minutos.</p>
        </Link>
      </div>

      {essays.length > 0 && (
        <div className="rounded-2xl border border-nerv-border bg-nerv-surface p-5">
          <h2 className="font-display font-bold">Evolução nas redações</h2>
          <div className="mt-3 flex items-end gap-2">
            {essays
              .slice(0, 10)
              .reverse()
              .map((e) => (
                <div key={e.id} className="flex flex-col items-center gap-1">
                  <div
                    className="w-8 rounded-t bg-nerv-purple"
                    style={{ height: `${Math.max(((e.nota_total ?? 0) / 1000) * 96, 4)}px` }}
                  />
                  <span className="text-[10px] text-nerv-muted">{e.nota_total}</span>
                </div>
              ))}
          </div>
        </div>
      )}
    </div>
  );
}
