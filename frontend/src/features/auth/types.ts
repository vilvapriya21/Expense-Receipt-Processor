/** A user's permission level. */
export type UserRole = "EMPLOYEE" | "ADMIN";

/** The currently authenticated user. */
export interface CurrentUser {
  id: number;
  email: string;
  fullName: string;
  role: UserRole;
}

/** Credentials submitted from the login form. */
export interface LoginCredentials {
  email: string;
  password: string;
}
