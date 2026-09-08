"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { Ambient } from "@/components/nerv/Ambient";
import { ProfessorNav } from "@/components/nerv/ProfessorNav";
import { useAuthStore } from "@/store/auth";

const STAFF_ROLES = ["teacher", "manager", "admin"];

export default function ProfessorLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const { accessToken, user, logout, hydrated } = useAuthStore();

  // Só decide depois que o localStorage foi lido: antes disso todo mundo
  // parece deslogado, e recarregar a página expulsaria da sessão.
  useEffect(() => {
    if (!hydrated) return;
    if (!accessToken) router.replace("/login");
    else if (user && !STAFF_ROLES.includes(user.role)) router.replace("/chat");
  }, [hydrated, accessToken, user, router]);

  if (!hydrated || !accessToken) return null;

  return (
    <div className="flex min-h-screen flex-col">
      <Ambient />
      <ProfessorNav
        nome={user?.name ?? "Professor"}
        role={user?.role ?? "teacher"}
        onLogout={() => {
          logout();
          router.replace("/login");
        }}
      />
      <main className="flex min-h-0 flex-1 flex-col">{children}</main>
    </div>
  );
}
