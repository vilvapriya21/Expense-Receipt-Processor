import axios, { type AxiosError } from "axios";

import { useAuthStore } from "@/features/auth/authStore";

/** A normalized API error shape, regardless of what the backend or network returned. */
export interface ApiError {
  code: string;
  message: string;
  details: Record<string, unknown>;
  status: number;
}

interface ErrorEnvelope {
  code?: string;
  message?: string;
  details?: Record<string, unknown>;
}

const baseURL =
  import.meta.env.VITE_API_BASE_URL?.trim() || "http://127.0.0.1:8000/api/v1";

export const httpClient = axios.create({ baseURL });

httpClient.interceptors.request.use((config) => {
  const { token } = useAuthStore.getState();
  if (token) {
    config.headers.set("Authorization", `Bearer ${token}`);
  }
  return config;
});

httpClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError<ErrorEnvelope>) => {
    const status = error.response?.status ?? 0;
    if (status === 401) {
      useAuthStore.getState().logout();
    }

    const apiError: ApiError = {
      code: error.response?.data?.code ?? "network_error",
      message: error.response?.data?.message ?? error.message,
      details: error.response?.data?.details ?? {},
      status,
    };
    return Promise.reject(apiError);
  },
);
