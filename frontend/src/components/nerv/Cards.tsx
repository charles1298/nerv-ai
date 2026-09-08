"use client";

// Cartoes de estatistica, acao e progresso.

import Link from "next/link";
import { motion } from "framer-motion";
import type { LucideIcon } from "lucide-react";
import { ArrowUpRight } from "lucide-react";

export function StatCard({
  label,
  value,
  suffix,
  icon: Icon,
  tone = "primary",
}: {
  label: string;
  value: string | number;
  suffix?: string;
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
    </motion.div>
  );
}

export function ActionCard({
  href,
  title,
  description,
  icon: Icon,
  cta,
}: {
  href: string;
  title: string;
  description: string;
  icon: LucideIcon;
  cta: string;
}) {
  return (
    <motion.div
      whileHover={{ y: -6 }}
      whileTap={{ scale: 0.985 }}
      transition={{ type: "spring", stiffness: 320, damping: 26 }}
      className="surface-card surface-card-hover group h-full"
    >
      <Link href={href} className="focus-nice flex h-full flex-col gap-3 rounded-2xl p-5 sm:p-6">
        <span className="grid size-11 place-items-center rounded-xl bg-primary/10 text-primary ring-1 ring-primary/25 transition-transform duration-500 group-hover:scale-110">
          <Icon className="size-5" />
        </span>
        <h3 className="text-lg font-semibold">{title}</h3>
        <p className="text-sm leading-relaxed text-muted-foreground">{description}</p>
        <span className="mt-auto inline-flex items-center gap-1.5 pt-2 text-sm font-semibold text-primary">
          {cta}
          <ArrowUpRight className="size-4 transition-transform duration-300 group-hover:-translate-y-0.5 group-hover:translate-x-0.5" />
        </span>
      </Link>
    </motion.div>
  );
}

export function ProgressBar({ value, label }: { value: number; label: string }) {
  return (
    <div>
      <div className="flex items-center justify-between text-sm">
        <span className="text-muted-foreground">{label}</span>
        <span className="font-semibold text-primary">{value}%</span>
      </div>
      <div className="mt-2 h-2.5 overflow-hidden rounded-full bg-surface-2">
        <motion.div
          className="h-full rounded-full bg-primary"
          initial={{ width: 0 }}
          animate={{ width: `${value}%` }}
          transition={{ duration: 1.1, ease: [0.22, 1, 0.36, 1] }}
        />
      </div>
    </div>
  );
}
