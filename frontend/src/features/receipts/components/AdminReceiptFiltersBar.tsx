import { MenuItem, Stack, TextField } from "@mui/material";

import { useCategories } from "@/features/categories/hooks/useCategories";
import { useEmployees } from "@/features/employees/hooks/useEmployees";

import type { AdminReceiptFilters, ReceiptStatus } from "../types";

const STATUS_OPTIONS: Array<{ value: ReceiptStatus | "ALL"; label: string }> = [
  { value: "ALL", label: "All statuses" },
  { value: "UPLOADED", label: "Uploaded" },
  { value: "EXTRACTED", label: "Extracted" },
  { value: "SUBMITTED", label: "Submitted" },
  { value: "APPROVED", label: "Approved" },
  { value: "REJECTED", label: "Rejected" },
];

/** Props for {@link AdminReceiptFiltersBar}. */
export interface AdminReceiptFiltersBarProps {
  /** The current filter values (excluding page/size). */
  filters: Omit<AdminReceiptFilters, "page" | "size">;
  /** Called with the updated filters whenever any field changes. */
  onChange: (filters: Omit<AdminReceiptFilters, "page" | "size">) => void;
}

/** Status/employee/category/date-range filters for the admin receipts table. */
export function AdminReceiptFiltersBar({ filters, onChange }: AdminReceiptFiltersBarProps) {
  const { data: employees = [] } = useEmployees();
  const { data: categories = [] } = useCategories();

  return (
    <Stack direction="row" spacing={2} flexWrap="wrap" useFlexGap sx={{ mb: 2 }}>
      <TextField
        select
        label="Status"
        id="admin-status-filter"
        value={filters.status ?? "ALL"}
        onChange={(event) => {
          const value = event.target.value as ReceiptStatus | "ALL";
          onChange({ ...filters, status: value === "ALL" ? undefined : value });
        }}
        sx={{ minWidth: 160 }}
      >
        {STATUS_OPTIONS.map((option) => (
          <MenuItem key={option.value} value={option.value}>
            {option.label}
          </MenuItem>
        ))}
      </TextField>
      <TextField
        select
        label="Employee"
        id="admin-employee-filter"
        value={filters.employeeId ?? ""}
        onChange={(event) => {
          const value = event.target.value;
          onChange({ ...filters, employeeId: value === "" ? undefined : Number(value) });
        }}
        sx={{ minWidth: 180 }}
      >
        <MenuItem value="">All employees</MenuItem>
        {employees.map((employee) => (
          <MenuItem key={employee.id} value={employee.id}>
            {employee.fullName}
          </MenuItem>
        ))}
      </TextField>
      <TextField
        select
        label="Category"
        id="admin-category-filter"
        value={filters.categoryId ?? ""}
        onChange={(event) => {
          const value = event.target.value;
          onChange({ ...filters, categoryId: value === "" ? undefined : Number(value) });
        }}
        sx={{ minWidth: 180 }}
      >
        <MenuItem value="">All categories</MenuItem>
        {categories.map((category) => (
          <MenuItem key={category.id} value={category.id}>
            {category.name}
          </MenuItem>
        ))}
      </TextField>
      <TextField
        label="From"
        id="admin-date-from-filter"
        type="date"
        slotProps={{ inputLabel: { shrink: true } }}
        value={filters.dateFrom ?? ""}
        onChange={(event) => onChange({ ...filters, dateFrom: event.target.value || undefined })}
      />
      <TextField
        label="To"
        id="admin-date-to-filter"
        type="date"
        slotProps={{ inputLabel: { shrink: true } }}
        value={filters.dateTo ?? ""}
        onChange={(event) => onChange({ ...filters, dateTo: event.target.value || undefined })}
      />
    </Stack>
  );
}
