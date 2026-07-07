"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/store/auth";

export default function Home() {
  const router = useRouter();
  const { accessToken, user } = useAuthStore();

  useEffect(() => {
    if (!accessToken) router.replace("/login");
    else if (user?.role === "student") router.replace("/dashboard");
    else router.replace("/turma");
  }, [accessToken, user, router]);

  return (
    <main className="flex min-h-screen items-center justify-center">
      <p className="font-display text-nerv-muted">Carregando NERV AI...</p>
    </main>
  );
}
