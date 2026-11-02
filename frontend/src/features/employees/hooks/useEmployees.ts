import { useQuery } from "@tanstack/react-query";

import { employeeService } from "../services/employeeService";

/**
 * Fetches the list of employees, for the admin receipts filter picker.
 *
 * @returns The TanStack Query result wrapping the list of employees.
 */
export function useEmployees() {
  return useQuery({
    queryKey: ["employees"],
    queryFn: employeeService.list,
  });
}
