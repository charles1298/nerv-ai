"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { Ambient } from "@/components/nerv/Ambient";
import { NervNav } from "@/components/nerv/NervNav";
import { useAuthStore } from "@/store/auth";

export default function AlunoLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const { accessToken, user, logout, hydrated } = useAuthStore();

  // Só decide depois que o localStorage foi lido: antes disso todo aluno
  // parece deslogado, e recarregar a página o expulsaria da sessão.
  useEffect(() => {
    if (hydrated && !accessToken) router.replace("/login");
  }, [hydrated, accessToken, router]);

  if (!hydrated || !accessToken) return null;

  return (
    <div className="flex min-h-screen flex-col">
      <Ambient />
      <NervNav
        studentName={user?.name ?? "Aluno"}
        onLogout={() => {
          logout();
          router.replace("/login");
        }}
      />
      {/* min-h-0 mantém o chat rolando dentro da própria área, sem esticar a página. */}
      <main className="flex min-h-0 flex-1 flex-col">{children}</main>
    </div>
  );
}
