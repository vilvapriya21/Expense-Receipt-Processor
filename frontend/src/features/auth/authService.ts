import { httpClient } from "@/services/httpClient";

import type { CurrentUser, LoginCredentials } from "./types";

interface LoginResponse {
  access_token: string;
  token_type: string;
}

interface CurrentUserResponse {
  id: number;
  email: string;
  full_name: string;
  role: "EMPLOYEE" | "ADMIN";
}

function mapCurrentUser(data: CurrentUserResponse): CurrentUser {
  return { id: data.id, email: data.email, fullName: data.full_name, role: data.role };
}

export const authService = {
  /** POST /auth/login — OAuth2 password flow; returns the signed access token. */
  async login(credentials: LoginCredentials): Promise<string> {
    const form = new URLSearchParams();
    form.set("username", credentials.email);
    form.set("password", credentials.password);
    const { data } = await httpClient.post<LoginResponse>("/auth/login", form, {
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
    });
    return data.access_token;
  },

  /** GET /auth/me — the currently authenticated user. */
  async getCurrentUser(): Promise<CurrentUser> {
    const { data } = await httpClient.get<CurrentUserResponse>("/auth/me");
    return mapCurrentUser(data);
  },
};
