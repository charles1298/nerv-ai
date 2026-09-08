"use client";

// Primitivos da área do professor, portados do pacote "AI Tutor Studio".
//
// Ficam separados dos componentes do aluno porque a densidade é outra: o
// professor lê muitos alunos de uma vez e precisa de métrica, painel e status
// compactos; o aluno lê uma coisa por vez.

import { motion } from "framer-motion";
import type { LucideIcon } from "lucide-react";
import type { ReactNode } from "react";
import type { StudentCard } from "@/lib/api";

export function PageHead({
  titulo,
  descricao,
  acao,
}: {
  titulo: ReactNode;
  descricao: string;
  acao?: ReactNode;
}) {
  return (
    <div className="flex flex-wrap items-end justify-between gap-4">
      <div>
        <h1 className="font-display text-2xl font-bold sm:text-3xl">{titulo}</h1>
        <p className="mt-1 max-w-xl text-sm leading-relaxed text-muted-foreground">{descricao}</p>
      </div>
      {acao}
    </div>
  );
}

export function PrimaryButton({
  children,
  icon: Icon,
  onClick,
  disabled,
  type = "button",
}: {
  children: ReactNode;
  icon?: LucideIcon;
  onClick?: () => void;
  disabled?: boolean;
  type?: "button" | "submit";
}) {
  return (
    <motion.button
      type={type}
      onClick={onClick}
      disabled={disabled}
      whileHover={disabled ? undefined : { y: -2 }}
      whileTap={disabled ? undefined : { scale: 0.97 }}
      transition={{ type: "spring", stiffness: 340, damping: 24 }}
      className="focus-nice shadow-lift inline-flex items-center gap-2 rounded-full bg-primary px-4 py-2.5 text-sm font-semibold text-primary-foreground transition-opacity duration-300 disabled:opacity-40"
    >
      {Icon ? <Icon className="size-4" /> : null}
      {children}
    </motion.button>
  );
}

export function GhostButton({
  children,
  icon: Icon,
  onClick,
  disabled,
  title,
}: {
  children: ReactNode;
  icon?: LucideIcon;
  onClick?: () => void;
  disabled?: boolean;
  title?: string;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      title={title}
      className="focus-nice inline-flex items-center gap-2 rounded-full border border-border px-3.5 py-2 text-sm font-medium text-muted-foreground transition-colors duration-300 hover:border-primary/40 hover:text-foreground disabled:opacity-40"
    >
      {Icon ? <Icon className="size-4" /> : null}
      {children}
    </button>
  );
}

export function Panel({
  titulo,
  acao,
  children,
  className,
}: {
  titulo?: string;
  acao?: ReactNode;
  children: ReactNode;
  className?: string;
}) {
  return (
    <section className={`surface-card p-5 sm:p-6 ${className ?? ""}`}>
      {titulo ? (
        <div className="mb-4 flex items-center justify-between gap-3">
          <h2 className="text-base font-semibold">{titulo}</h2>
          {acao}
        </div>
      ) : null}
      {children}
    </section>
  );
}

export function Metric({
  label,
  value,
  suffix,
  hint,
  icon: Icon,
  tone = "primary",
}: {
  label: string;
  value: string | number;
  suffix?: string;
  hint?: string;
  icon: LucideIcon;
  tone?: "primary" | "streak" | "badge" | "muted";
}) {
  const toneClass = {
    primary: "text-xp",
    streak: "text-streak",
    badge: "text-badge",
    muted: "text-muted-foreground",
  }[tone];

  return (
    <motion.div
      whileHover={{ y: -4 }}
      transition={{ type: "spring", stiffness: 320, damping: 26 }}
      className="surface-card p-4 sm:p-5"
    >
      <div className="flex items-center gap-2 text-xs uppercase tracking-wide text-muted-foreground">
        <Icon className={`size-4 shrink-0 ${toneClass}`} />
        <span className="truncate">{label}</span>
      </div>
      <p className="mt-3 font-display text-3xl font-bold">
        <span className={toneClass}>{value}</span>
        {suffix ? (
          <span className="ml-1.5 text-sm font-medium text-muted-foreground">{suffix}</span>
        ) : null}
      </p>
      {hint ? <p className="mt-1 text-xs text-muted-foreground">{hint}</p> : null}
    </motion.div>
  );
}

export function Bar({ pct, label, right }: { pct: number; label: string; right?: string }) {
  return (
    <div>
      <div className="flex items-center justify-between text-sm">
        <span className="text-muted-foreground">{label}</span>
        <span className="font-semibold text-primary">{right ?? `${pct}%`}</span>
      </div>
      <div className="mt-2 h-2 overflow-hidden rounded-full bg-surface-2">
        <motion.div
          className="h-full rounded-full bg-primary"
          initial={{ width: 0 }}
          animate={{ width: `${Math.min(100, Math.max(0, pct))}%` }}
          transition={{ duration: 1, ease: [0.22, 1, 0.36, 1] }}
        />
      </div>
    </div>
  );
}

/**
 * Status do aluno na turma.
 *
 * Os rótulos vêm da API (`em_dia | atencao | critico`) e não do pacote, que usa
 * outro conjunto. Traduzir aqui evita espalhar o mapeamento pelas telas.
 */
export function StatusPill({ status }: { status: StudentCard["status"] }) {
  const map: Record<StudentCard["status"], { label: string; cls: string }> = {
    em_dia: { label: "Em dia", cls: "border-primary/40 bg-primary/10 text-primary" },
    atencao: { label: "Atenção", cls: "border-streak/40 bg-streak/10 text-streak" },
    critico: { label: "Crítico", cls: "border-destructive/40 bg-destructive/10 text-destructive" },
  };
  const { label, cls } = map[status] ?? map.atencao;

  return (
    <span
      className={`inline-flex shrink-0 items-center rounded-full border px-2.5 py-1 text-xs font-semibold ${cls}`}
    >
      {label}
    </span>
  );
}

export function Tag({ children }: { children: ReactNode }) {
  return (
    <span className="inline-flex items-center rounded-full border border-border bg-surface-2/60 px-2.5 py-1 text-xs font-medium text-muted-foreground">
      {children}
    </span>
  );
}
