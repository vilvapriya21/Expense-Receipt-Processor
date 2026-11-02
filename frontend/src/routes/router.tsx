import { Box, CircularProgress } from "@mui/material";
import { lazy, Suspense, type ReactNode } from "react";
import { createBrowserRouter, Navigate } from "react-router-dom";

import { ErrorBoundary } from "@/components/ErrorBoundary";
import { Layout } from "@/components/Layout";

import { RoleGuard } from "./RoleGuard";

const LoginPage = lazy(() => import("@/pages/LoginPage"));
const EmployeeDashboardPage = lazy(() => import("@/pages/EmployeeDashboardPage"));
const UploadReceiptPage = lazy(() => import("@/pages/UploadReceiptPage"));
const ReviewReceiptPage = lazy(() => import("@/pages/ReviewReceiptPage"));
const MyReceiptsPage = lazy(() => import("@/pages/MyReceiptsPage"));
const AdminDashboardPage = lazy(() => import("@/pages/AdminDashboardPage"));
const AdminReceiptsPage = lazy(() => import("@/pages/AdminReceiptsPage"));
const AdminCategoriesPage = lazy(() => import("@/pages/AdminCategoriesPage"));
const AdminSummariesPage = lazy(() => import("@/pages/AdminSummariesPage"));
const NotFoundPage = lazy(() => import("@/pages/NotFoundPage"));

function withSuspense(element: ReactNode): ReactNode {
  return (
    <Suspense
      fallback={
        <Box sx={{ display: "flex", justifyContent: "center", p: 4 }}>
          <CircularProgress />
        </Box>
      }
    >
      {element}
    </Suspense>
  );
}

export const router = createBrowserRouter([
  {
    path: "/login",
    element: withSuspense(<LoginPage />),
  },
  {
    path: "/",
    element: (
      <ErrorBoundary>
        <Layout />
      </ErrorBoundary>
    ),
    children: [
      { index: true, element: <Navigate to="/employee" replace /> },
      {
        path: "employee",
        element: (
          <RoleGuard allowedRoles={["EMPLOYEE"]}>
            {withSuspense(<EmployeeDashboardPage />)}
          </RoleGuard>
        ),
      },
      {
        path: "employee/upload",
        element: (
          <RoleGuard allowedRoles={["EMPLOYEE"]}>{withSuspense(<UploadReceiptPage />)}</RoleGuard>
        ),
      },
      {
        path: "employee/receipts",
        element: (
          <RoleGuard allowedRoles={["EMPLOYEE"]}>{withSuspense(<MyReceiptsPage />)}</RoleGuard>
        ),
      },
      {
        path: "employee/receipts/:receiptId/review",
        element: (
          <RoleGuard allowedRoles={["EMPLOYEE"]}>{withSuspense(<ReviewReceiptPage />)}</RoleGuard>
        ),
      },
      {
        path: "admin",
        element: (
          <RoleGuard allowedRoles={["ADMIN"]}>{withSuspense(<AdminDashboardPage />)}</RoleGuard>
        ),
      },
      {
        path: "admin/receipts",
        element: (
          <RoleGuard allowedRoles={["ADMIN"]}>{withSuspense(<AdminReceiptsPage />)}</RoleGuard>
        ),
      },
      {
        path: "admin/categories",
        element: (
          <RoleGuard allowedRoles={["ADMIN"]}>{withSuspense(<AdminCategoriesPage />)}</RoleGuard>
        ),
      },
      {
        path: "admin/summaries",
        element: (
          <RoleGuard allowedRoles={["ADMIN"]}>{withSuspense(<AdminSummariesPage />)}</RoleGuard>
        ),
      },
      { path: "*", element: withSuspense(<NotFoundPage />) },
    ],
  },
]);
