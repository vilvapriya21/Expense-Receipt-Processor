import type { CategoryTotal } from "@/features/receipts/types";

/** Total approved amount and count for a single calendar month. */
export interface MonthTotal {
  month: string;
  totalAmount: number;
  count: number;
}

/** Total approved amount and count for a single employee. */
export interface EmployeeTotal {
  employeeId: number;
  employeeName: string;
  totalAmount: number;
  count: number;
}

/** Finance-wide receipt totals, across all employees, for an optional date range. */
export interface AdminSummary {
  countsByStatus: Record<string, number>;
  taxTotal: number;
  byCategory: CategoryTotal[];
  byMonth: MonthTotal[];
  byEmployee: EmployeeTotal[];
}

/** Date range filter for the admin summaries page. */
export interface SummaryDateRange {
  dateFrom?: string;
  dateTo?: string;
}
