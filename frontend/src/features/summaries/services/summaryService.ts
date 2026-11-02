import { httpClient } from "@/services/httpClient";
import type { CategoryTotal } from "@/features/receipts/types";

import type { AdminSummary, EmployeeTotal, MonthTotal, SummaryDateRange } from "../types";

interface CategoryTotalResponse {
  category_id: number | null;
  category_name: string | null;
  total_amount: string;
  count: number;
}

interface MonthTotalResponse {
  month: string;
  total_amount: string;
  count: number;
}

interface EmployeeTotalResponse {
  employee_id: number;
  employee_name: string;
  total_amount: string;
  count: number;
}

interface AdminSummaryResponse {
  counts_by_status: Record<string, number>;
  tax_total: string;
  by_category: CategoryTotalResponse[];
  by_month: MonthTotalResponse[];
  by_employee: EmployeeTotalResponse[];
}

function mapCategoryTotal(data: CategoryTotalResponse): CategoryTotal {
  return {
    categoryId: data.category_id,
    categoryName: data.category_name,
    totalAmount: Number(data.total_amount),
    count: data.count,
  };
}

function mapMonthTotal(data: MonthTotalResponse): MonthTotal {
  return { month: data.month, totalAmount: Number(data.total_amount), count: data.count };
}

function mapEmployeeTotal(data: EmployeeTotalResponse): EmployeeTotal {
  return {
    employeeId: data.employee_id,
    employeeName: data.employee_name,
    totalAmount: Number(data.total_amount),
    count: data.count,
  };
}

export const summaryService = {
  /** GET /admin/summaries — finance-wide totals by category/month/employee (admin-only). */
  async getAdminSummary(range: SummaryDateRange): Promise<AdminSummary> {
    const { data } = await httpClient.get<AdminSummaryResponse>("/admin/summaries", {
      params: { date_from: range.dateFrom, date_to: range.dateTo },
    });
    return {
      countsByStatus: data.counts_by_status,
      taxTotal: Number(data.tax_total),
      byCategory: data.by_category.map(mapCategoryTotal),
      byMonth: data.by_month.map(mapMonthTotal),
      byEmployee: data.by_employee.map(mapEmployeeTotal),
    };
  },
};
