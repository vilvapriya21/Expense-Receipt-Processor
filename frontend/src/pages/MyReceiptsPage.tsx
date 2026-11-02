import { Alert, MenuItem, Paper, Stack, TextField } from "@mui/material";
import { useState } from "react";

import { LoadingState } from "@/components/LoadingState";
import { PageHeader } from "@/components/PageHeader";
import { ReceiptsTable } from "@/features/receipts/components/ReceiptsTable";
import { useReceiptsList } from "@/features/receipts/hooks/useReceipts";
import type { ReceiptStatus } from "@/features/receipts/types";

const PAGE_SIZE = 10;

const STATUS_OPTIONS: Array<{ value: ReceiptStatus | "ALL"; label: string }> = [
  { value: "ALL", label: "All statuses" },
  { value: "UPLOADED", label: "Uploaded" },
  { value: "EXTRACTED", label: "Extracted" },
  { value: "SUBMITTED", label: "Submitted" },
  { value: "APPROVED", label: "Approved" },
  { value: "REJECTED", label: "Rejected" },
];

/** The employee's own receipts: a filterable, paginated table. */
export default function MyReceiptsPage() {
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState<ReceiptStatus | "ALL">("ALL");

  const { data, isLoading, isError } = useReceiptsList({
    page,
    size: PAGE_SIZE,
    status: statusFilter === "ALL" ? undefined : statusFilter,
  });

  const pageCount = data ? Math.max(1, Math.ceil(data.total / PAGE_SIZE)) : 1;

  return (
    <Stack spacing={3}>
      <PageHeader title="My Receipts" />
      <TextField
        select
        label="Status"
        id="status-filter"
        value={statusFilter}
        onChange={(event) => {
          setStatusFilter(event.target.value as ReceiptStatus | "ALL");
          setPage(1);
        }}
        sx={{ maxWidth: 240 }}
      >
        {STATUS_OPTIONS.map((option) => (
          <MenuItem key={option.value} value={option.value}>
            {option.label}
          </MenuItem>
        ))}
      </TextField>
      {isLoading && <LoadingState label="Loading your receipts…" />}
      {isError && <Alert severity="error">Could not load your receipts.</Alert>}
      {data && (
        <Paper variant="outlined" sx={{ p: 2 }}>
          <ReceiptsTable
            receipts={data.items}
            page={page}
            pageCount={pageCount}
            onPageChange={setPage}
          />
        </Paper>
      )}
    </Stack>
  );
}
