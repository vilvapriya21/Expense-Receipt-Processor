/** Route paths used throughout the app, kept in one place to avoid typos. */
export const ROUTES = {
  login: "/login",
  employeeDashboard: "/employee",
  employeeUpload: "/employee/upload",
  employeeReceipts: "/employee/receipts",
  employeeReview: (receiptId: number | string): string =>
    `/employee/receipts/${receiptId}/review`,
  adminDashboard: "/admin",
} as const;
