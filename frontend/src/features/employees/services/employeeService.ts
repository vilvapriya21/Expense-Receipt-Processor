import { httpClient } from "@/services/httpClient";

import type { Employee } from "../types";

interface EmployeeResponse {
  id: number;
  email: string;
  full_name: string;
}

function mapEmployee(data: EmployeeResponse): Employee {
  return { id: data.id, email: data.email, fullName: data.full_name };
}

export const employeeService = {
  /** GET /admin/employees — every employee, for the admin receipts filter picker. */
  async list(): Promise<Employee[]> {
    const { data } = await httpClient.get<EmployeeResponse[]>("/admin/employees");
    return data.map(mapEmployee);
  },
};
