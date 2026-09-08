"use client";

// Navegação da área do professor, portada do pacote "AI Tutor Studio".
//
// Diferença em relação à do aluno: aqui são muitas seções, então no desktop a
// pílula desliza numa barra e no mobile vira uma faixa rolável presa abaixo do
// cabeçalho — em vez da tab bar de 4 itens no rodapé, que não caberia.

import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion } from "framer-motion";
import {
  BookMarked,
  Building2,
  ClipboardList,
  HelpCircle,
  LayoutDashboard,
  LogOut,
  Sparkles,
  Users,
  type LucideIcon,
} from "lucide-react";
import { NervLogo } from "./NervLogo";

interface ItemNav {
  href: string;
  label: string;
  icon: LucideIcon;
  /** Seção sem backend ainda: marcada na navegação para não prometer o que não faz. */
  emBreve?: boolean;
  /** Só gestor e admin enxergam a visão da escola inteira. */
  somenteGestao?: boolean;
}

const ITENS: ItemNav[] = [
  { href: "/turma", label: "Painel", icon: LayoutDashboard },
  { href: "/alunos", label: "Alunos", icon: Users },
  { href: "/escola", label: "Escola", icon: Building2, somenteGestao: true },
  { href: "/tarefas", label: "Tarefas", icon: ClipboardList, emBreve: true },
  { href: "/materiais", label: "Materiais", icon: BookMarked, emBreve: true },
  { href: "/duvidas", label: "Dúvidas", icon: HelpCircle, emBreve: true },
  { href: "/nerv", label: "NERV", icon: Sparkles, emBreve: true },
];

export function ProfessorNav({
  nome = "Professor",
  role = "teacher",
  onLogout,
}: {
  nome?: string;
  role?: string;
  onLogout?: () => void;
}) {
  const pathname = usePathname();
  const inicial = nome.trim().charAt(0).toUpperCase() || "P";
  const ehGestao = role === "manager" || role === "admin";
  const itens = ITENS.filter((i) => !i.somenteGestao || ehGestao);
  const papel = ehGestao ? "Gestão" : "Professor";

  return (
    <>
      <header className="sticky top-0 z-40 border-b border-border bg-background/70 backdrop-blur-xl">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-3 px-4 py-3">
          <div className="flex min-w-0 items-center gap-3">
            <NervLogo href="/turma" />
            <span className="hidden rounded-full border border-primary/30 bg-primary/10 px-2.5 py-1 text-[0.7rem] font-semibold uppercase tracking-wide text-primary sm:inline">
              {papel}
            </span>
          </div>

          <nav className="hidden items-center gap-1 rounded-full border border-border bg-surface/70 p-1 lg:flex">
            {itens.map((item) => {
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className="focus-nice relative rounded-full px-3.5 py-2 text-sm font-medium text-muted-foreground transition-colors duration-300 hover:text-foreground"
                >
                  {isActive ? (
                    <motion.span
                      layoutId="prof-nav-pill"
                      className="absolute inset-0 rounded-full bg-primary/15 ring-1 ring-primary/40"
                      transition={{ type: "spring", stiffness: 380, damping: 32 }}
                    />
                  ) : null}
                  <span
                    className={`relative inline-flex items-center gap-1.5 ${
                      isActive ? "text-foreground" : ""
                    }`}
                  >
                    {item.label}
                    {item.emBreve && (
                      <span
                        aria-hidden
                        title="Em breve"
                        className="size-1.5 rounded-full bg-muted-foreground/60"
                      />
                    )}
                  </span>
                </Link>
              );
            })}
          </nav>

          <div className="flex min-w-0 items-center gap-2">
            <span className="hidden truncate text-sm text-muted-foreground sm:inline">{nome}</span>
            <span className="grid size-9 shrink-0 place-items-center rounded-full bg-primary/15 font-display text-sm font-bold text-primary ring-1 ring-primary/30">
              {inicial}
            </span>
            <button
              type="button"
              onClick={onLogout}
              className="focus-nice hidden items-center gap-1.5 rounded-full border border-border px-3 py-2 text-sm text-muted-foreground transition-colors duration-300 hover:border-primary/40 hover:text-foreground sm:inline-flex"
            >
              <LogOut className="size-4" /> Sair
            </button>
          </div>
        </div>
      </header>

      {/* Faixa rolável para telas menores: sete seções não cabem numa tab bar. */}
      <nav className="sticky top-[3.75rem] z-30 border-b border-border bg-background/80 backdrop-blur-xl lg:hidden">
        <div className="mx-auto flex max-w-6xl gap-1 overflow-x-auto px-3 py-2">
          {itens.map((item) => {
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`focus-nice inline-flex shrink-0 items-center gap-1.5 rounded-full border px-3 py-1.5 text-sm font-medium transition-colors duration-300 ${
                  isActive
                    ? "border-primary/40 bg-primary/10 text-primary"
                    : "border-transparent text-muted-foreground"
                }`}
              >
                <item.icon className="size-4" />
                {item.label}
                {item.emBreve && (
                  <span aria-hidden className="size-1.5 rounded-full bg-muted-foreground/60" />
                )}
              </Link>
            );
          })}
        </div>
      </nav>
    </>
  );
}
