"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { api, ApiError } from "@/lib/api";
import { DEMO } from "@/lib/demo";
import { useAuthStore } from "@/store/auth";

interface LoginForm {
  email: string;
  password: string;
}

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
    <main className="flex min-h-screen items-center justify-center px-4">
      <div className="w-full max-w-md rounded-2xl border border-nerv-border bg-nerv-surface p-8">
        <h1 className="font-display text-3xl font-bold text-nerv-purple">
          NERV<span className="text-nerv-neon">.AI</span>
        </h1>
        <p className="mt-1 text-sm text-nerv-muted">
          Seu tutor infinitamente paciente, disponível 24h.
        </p>

        {DEMO && (
          <div className="mt-4 rounded-lg border border-nerv-neon/40 bg-nerv-neon/5 p-3 text-xs text-nerv-muted">
            <span className="font-display font-bold text-nerv-neon">Modo demonstração.</span>{" "}
            Entre com qualquer senha e um destes e-mails para explorar cada perfil:
            <br />
            <span className="text-nerv-text">aluno@demo.nerv.ai</span> ·{" "}
            <span className="text-nerv-text">professora@demo.nerv.ai</span> ·{" "}
            <span className="text-nerv-text">gestor@demo.nerv.ai</span>
          </div>
        )}

        <form onSubmit={handleSubmit(onSubmit)} className="mt-8 space-y-4">
          <div>
            <label htmlFor="email" className="text-sm text-nerv-muted">
              E-mail
            </label>
            <input
              id="email"
              type="email"
              autoComplete="email"
              {...register("email", { required: true })}
              className="mt-1 w-full rounded-lg border border-nerv-border bg-nerv-bg px-3 py-2 outline-none focus:border-nerv-purple"
            />
          </div>
          <div>
            <label htmlFor="password" className="text-sm text-nerv-muted">
              Senha
            </label>
            <input
              id="password"
              type="password"
              autoComplete="current-password"
              {...register("password", { required: true })}
              className="mt-1 w-full rounded-lg border border-nerv-border bg-nerv-bg px-3 py-2 outline-none focus:border-nerv-purple"
            />
          </div>

          {error && <p className="text-sm text-red-400">{error}</p>}

          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full rounded-lg bg-nerv-purple py-2.5 font-display font-medium transition hover:bg-nerv-purple-dim disabled:opacity-50"
          >
            {isSubmitting ? "Entrando..." : "Entrar"}
          </button>
        </form>
      </div>
    </main>
  );
}
