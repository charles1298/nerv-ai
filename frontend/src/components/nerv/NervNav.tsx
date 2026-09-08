"use client";

// Barra de navegacao do aluno: pilula deslizante no desktop, tab bar no celular.

import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion } from "framer-motion";
import { Home, MessageCircle, ListChecks, PenLine, LogOut } from "lucide-react";
import { NervLogo } from "./NervLogo";

const items = [
  { href: "/dashboard", label: "Início", icon: Home },
  { href: "/chat", label: "Tutoria", icon: MessageCircle },
  { href: "/exercicios", label: "Exercícios", icon: ListChecks },
  { href: "/redacao", label: "Redação", icon: PenLine },
] as const;

export function NervNav({
  studentName = "Aluno",
  onLogout,
}: {
  studentName?: string;
  onLogout?: () => void;
}) {
  const pathname = usePathname();
  const inicial = studentName.trim().charAt(0).toUpperCase() || "A";

  return (
    <>
      <header className="sticky top-0 z-40 border-b border-border bg-background/70 backdrop-blur-xl">
        <div className="mx-auto grid max-w-6xl grid-cols-[minmax(0,1fr)_auto] items-center gap-3 px-4 py-3 sm:flex sm:justify-between">
          <NervLogo />

          <nav className="hidden items-center gap-1 rounded-full border border-border bg-surface/70 p-1 md:flex">
            {items.map((item) => {
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className="focus-nice relative rounded-full px-4 py-2 text-sm font-medium text-muted-foreground transition-colors duration-300 hover:text-foreground"
                >
                  {isActive ? (
                    <motion.span
                      layoutId="nav-pill"
                      className="absolute inset-0 rounded-full bg-primary/15 ring-1 ring-primary/40"
                      transition={{ type: "spring", stiffness: 380, damping: 32 }}
                    />
                  ) : null}
                  <span className={isActive ? "relative text-foreground" : "relative"}>
                    {item.label}
                  </span>
                </Link>
              );
            })}
          </nav>

          <div className="flex min-w-0 items-center justify-end gap-2">
            <span className="hidden truncate text-sm text-muted-foreground sm:inline">
              {studentName}
            </span>
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

      {/* Tab bar do celular — um toque, sem atrito. */}
      <nav className="fixed inset-x-0 bottom-0 z-40 border-t border-border bg-background/90 backdrop-blur-xl md:hidden">
        <div className="mx-auto flex max-w-md items-stretch justify-between px-2 py-1.5">
          {items.map((item) => {
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`focus-nice flex flex-1 flex-col items-center gap-1 rounded-xl py-2 text-[0.7rem] font-medium transition-colors duration-300 ${
                  isActive ? "text-primary" : "text-muted-foreground"
                }`}
              >
                <item.icon className="size-5" />
                {item.label}
              </Link>
            );
          })}
        </div>
      </nav>
    </>
  );
}
