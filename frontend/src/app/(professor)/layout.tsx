"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { useAuthStore } from "@/store/auth";

const STAFF_ROLES = ["teacher", "manager", "admin"];

export default function ProfessorLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const { accessToken, user, logout } = useAuthStore();

  useEffect(() => {
    if (!accessToken) router.replace("/login");
    else if (user && !STAFF_ROLES.includes(user.role)) router.replace("/chat");
  }, [accessToken, user, router]);

  if (!accessToken) return null;

  return (
    <div className="flex h-screen flex-col">
      <header className="flex items-center justify-between border-b border-nerv-border px-6 py-3">
        <Link href="/turma" className="font-display text-xl font-bold text-nerv-purple">
          NERV<span className="text-nerv-neon">.AI</span>
          <span className="ml-2 text-xs font-normal text-nerv-muted">painel docente</span>
        </Link>
        <nav className="flex items-center gap-6 text-sm">
          <Link href="/turma" className="text-nerv-muted transition hover:text-nerv-text">
            Turma
          </Link>
          {(user?.role === "manager" || user?.role === "admin") && (
            <Link href="/escola" className="text-nerv-muted transition hover:text-nerv-text">
              Escola
            </Link>
          )}
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
      <main className="min-h-0 flex-1 overflow-y-auto">{children}</main>
    </div>
  );
}
