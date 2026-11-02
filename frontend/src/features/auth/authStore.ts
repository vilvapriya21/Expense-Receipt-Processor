import { create } from "zustand";
import { persist } from "zustand/middleware";

import type { CurrentUser } from "./types";

interface AuthState {
  token: string | null;
  user: CurrentUser | null;
  setToken: (token: string) => void;
  setSession: (token: string, user: CurrentUser) => void;
  logout: () => void;
}

/** Session state: the bearer token and the current user. Persisted to localStorage. */
export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      user: null,
      setToken: (token) => set({ token }),
      setSession: (token, user) => set({ token, user }),
      logout: () => set({ token: null, user: null }),
    }),
    { name: "auth-storage" },
  ),
);
