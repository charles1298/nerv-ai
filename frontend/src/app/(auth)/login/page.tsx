"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { LogIn } from "lucide-react";
import { api, ApiError } from "@/lib/api";
import { DEMO } from "@/lib/demo";
import { useAuthStore } from "@/store/auth";
import { Ambient } from "@/components/nerv/Ambient";
import { Reveal } from "@/components/nerv/Reveal";

interface LoginForm {
  email: string;
  password: string;
}

const campo =
  "mt-1 w-full rounded-xl border border-border bg-background/60 px-3.5 py-2.5 text-sm outline-none transition-colors duration-300 placeholder:text-muted-foreground focus:border-primary/60";

export default function LoginPage() {
  const router = useRouter();
  const { setTokens, setUser } = useAuthStore();
  const [error, setError] = useState<string | null>(null);
  const {
    register,
    handleSubmit,
    formState: { isSubmitting },
  } = useForm<LoginForm>();

  const onSubmit = async (data: LoginForm) => {
    setError(null);
    try {
      const tokens = await api.login(data.email, data.password);
      setTokens(tokens.access_token, tokens.refresh_token);
      const me = await api.me();
      setUser(me);
      router.push(me.role === "student" ? "/dashboard" : "/turma");
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Erro inesperado. Tente novamente.");
    }
  };

  return (
    <main className="flex min-h-screen items-center justify-center px-4 py-10">
      <Ambient />

      <Reveal className="w-full max-w-md">
        <div className="surface-card glow-ring p-8">
          <div className="flex flex-col items-center text-center">
            <span className="relative grid size-16 place-items-center">
              <span className="absolute inset-0 animate-pulse-glow rounded-full bg-primary/25 blur-lg" />
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src="/nerv-mark.png"
                alt="NERV.AI"
                width={512}
                height={512}
                className="relative size-14 animate-float"
              />
            </span>
            <h1 className="mt-4 font-display text-3xl font-bold tracking-tight">
              NERV<span className="text-gradient">.AI</span>
            </h1>
            <p className="mt-1.5 text-sm text-muted-foreground">
              Seu tutor infinitamente paciente, disponível 24h.
            </p>
          </div>

          {DEMO && (
            <div className="mt-6 rounded-xl border border-border bg-primary/5 p-3 text-xs text-muted-foreground">
              <span className="font-display font-bold text-primary">Modo demonstração.</span> Entre
              com qualquer senha e um destes e-mails para explorar cada perfil:
              <br />
              <span className="text-foreground">aluno@demo.nerv.ai</span> ·{" "}
              <span className="text-foreground">professora@demo.nerv.ai</span> ·{" "}
              <span className="text-foreground">gestor@demo.nerv.ai</span>
            </div>
          )}

          <form onSubmit={handleSubmit(onSubmit)} className="mt-7 space-y-4">
            <div>
              <label htmlFor="email" className="text-sm text-muted-foreground">
                E-mail
              </label>
              <input
                id="email"
                type="email"
                autoComplete="email"
                placeholder="voce@escola.com.br"
                {...register("email", { required: true })}
                className={campo}
              />
            </div>
            <div>
              <label htmlFor="password" className="text-sm text-muted-foreground">
                Senha
              </label>
              <input
                id="password"
                type="password"
                autoComplete="current-password"
                placeholder="••••••••"
                {...register("password", { required: true })}
                className={campo}
              />
            </div>

            {error && (
              <p className="text-sm text-destructive" role="alert">
                {error}
              </p>
            )}

            <button
              type="submit"
              disabled={isSubmitting}
              className="focus-nice inline-flex w-full items-center justify-center gap-2 rounded-xl bg-primary py-2.5 font-display font-semibold text-primary-foreground transition-opacity duration-300 hover:opacity-90 disabled:opacity-50"
            >
              <LogIn className="size-4" />
              {isSubmitting ? "Entrando..." : "Entrar"}
            </button>
          </form>
        </div>
      </Reveal>
    </main>
  );
}
