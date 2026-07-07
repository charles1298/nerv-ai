// Estado global de autenticação (Zustand) com persistência em localStorage.

import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { UserPublic } from "@/lib/api";

interface AuthState {
  accessToken: string | null;
  refreshToken: string | null;
  user: UserPublic | null;
  setTokens: (access: string, refresh: string) => void;
  setUser: (user: UserPublic) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      accessToken: null,
      refreshToken: null,
      user: null,
      setTokens: (access, refresh) =>
        set({ accessToken: access, refreshToken: refresh }),
      setUser: (user) => set({ user }),
      logout: () => set({ accessToken: null, refreshToken: null, user: null }),
    }),
    { name: "nerv-auth" },
  ),
);
