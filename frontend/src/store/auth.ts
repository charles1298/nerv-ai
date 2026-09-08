// Estado global de autenticação (Zustand) com persistência em localStorage.

import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { UserPublic } from "@/lib/api";

interface AuthState {
  accessToken: string | null;
  refreshToken: string | null;
  user: UserPublic | null;
  /**
   * Se o estado já veio do localStorage.
   *
   * O primeiro render no navegador precisa bater com o HTML gerado no
   * servidor, onde não existe localStorage — então o token nasce nulo e só
   * aparece no render seguinte. Sem este sinal, os layouts protegidos leem
   * "sem token" nesse instante e mandam o aluno para o login: recarregar a
   * página ou abrir um link direto derrubava a sessão.
   */
  hydrated: boolean;
  setTokens: (access: string, refresh: string) => void;
  setUser: (user: UserPublic) => void;
  setHydrated: () => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      accessToken: null,
      refreshToken: null,
      user: null,
      hydrated: false,
      setTokens: (access, refresh) => set({ accessToken: access, refreshToken: refresh }),
      setUser: (user) => set({ user }),
      setHydrated: () => set({ hydrated: true }),
      logout: () => set({ accessToken: null, refreshToken: null, user: null }),
    }),
    {
      name: "nerv-auth",
      // Só o que é do usuário é persistido. `hydrated` descreve o carregamento:
      // gravá-lo faria a próxima visita começar já marcada como hidratada, o
      // que traria o bug de volta.
      partialize: ({ accessToken, refreshToken, user }) => ({ accessToken, refreshToken, user }),
      // Dispara mesmo quando não há nada salvo, que é justamente o caso em que
      // o redirecionamento para o login precisa acontecer.
      onRehydrateStorage: () => (state) => state?.setHydrated(),
    },
  ),
);
