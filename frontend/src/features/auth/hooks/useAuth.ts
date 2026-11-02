import { useMutation } from "@tanstack/react-query";

import { authService } from "../authService";
import { useAuthStore } from "../authStore";
import type { LoginCredentials } from "../types";

/**
 * Logs in, then fetches the current user, then stores both in the auth store.
 *
 * @returns The TanStack Query mutation object for triggering and observing login.
 */
export function useLogin() {
  const setToken = useAuthStore((state) => state.setToken);
  const setSession = useAuthStore((state) => state.setSession);

  return useMutation({
    mutationFn: async (credentials: LoginCredentials) => {
      const token = await authService.login(credentials);
      setToken(token);
      const user = await authService.getCurrentUser();
      return { token, user };
    },
    onSuccess: ({ token, user }) => {
      setSession(token, user);
    },
  });
}

/** Logs the current user out, clearing the auth store. */
export function useLogout() {
  const logout = useAuthStore((state) => state.logout);
  return logout;
}
