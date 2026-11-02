import { QueryClient } from "@tanstack/react-query";

/** The shared TanStack Query client, holding all server-state cache. */
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});
