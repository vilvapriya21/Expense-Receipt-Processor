import type { ReactNode } from "react";
import { Navigate } from "react-router-dom";

import { useAuthStore } from "@/features/auth/authStore";
import type { UserRole } from "@/features/auth/types";

/** Props for {@link RoleGuard}. */
export interface RoleGuardProps {
  /** Roles allowed to view the wrapped route. */
  allowedRoles: UserRole[];
  /** The route content to render when authorized. */
  children: ReactNode;
}

/** Redirects to /login when unauthenticated, or to the user's own area on a role mismatch. */
export function RoleGuard({ allowedRoles, children }: RoleGuardProps) {
  const user = useAuthStore((state) => state.user);

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  if (!allowedRoles.includes(user.role)) {
    const fallback = user.role === "ADMIN" ? "/admin" : "/employee";
    return <Navigate to={fallback} replace />;
  }

  return children;
}
