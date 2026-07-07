"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { useAuthStore } from "@/store/auth";

export default function AlunoLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const { accessToken, user, logout } = useAuthStore();

  useEffect(() => {
    if (!accessToken) router.replace("/login");
  }, [accessToken, router]);

  if (!accessToken) return null;

  return (
    <div className="flex h-screen flex-col">
      <header className="flex items-center justify-between border-b border-nerv-border px-6 py-3">
        <Link href="/chat" className="font-display text-xl font-bold text-nerv-purple">
          NERV<span className="text-nerv-neon">.AI</span>
        </Link>
        <nav className="flex items-center gap-6 text-sm">
          <Link href="/dashboard" className="text-nerv-muted transition hover:text-nerv-text">
            Início
          </Link>
          <Link href="/chat" className="text-nerv-muted transition hover:text-nerv-text">
            Tutoria
          </Link>
          <Link href="/exercicios" className="text-nerv-muted transition hover:text-nerv-text">
            Exercícios
          </Link>
          <Link href="/redacao" className="text-nerv-muted transition hover:text-nerv-text">
            Redação
          </Link>
          <span className="text-nerv-muted">{user?.name}</span>
          <button
            onClick={() => {
              logout();
              router.replace("/login");
            }}
            className="rounded-lg border border-nerv-border px-3 py-1.5 text-nerv-muted transition hover:border-nerv-purple hover:text-nerv-text"
          >
            Sair
          </button>
        </nav>
      </header>
      <main className="min-h-0 flex-1">{children}</main>
    </div>
  );
}
