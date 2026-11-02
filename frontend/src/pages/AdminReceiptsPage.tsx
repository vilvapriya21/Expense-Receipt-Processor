import { Alert, Paper, Stack } from "@mui/material";
import { useState } from "react";

import { LoadingState } from "@/components/LoadingState";
import { PageHeader } from "@/components/PageHeader";
import { AdminReceiptFiltersBar } from "@/features/receipts/components/AdminReceiptFiltersBar";
import { AdminReceiptsTable } from "@/features/receipts/components/AdminReceiptsTable";
import { ReceiptDetailDrawer } from "@/features/receipts/components/ReceiptDetailDrawer";
import {
  useAdminReceiptsList,
  useApproveReceipt,
  useRejectReceipt,
} from "@/features/receipts/hooks/useReceipts";
import type { AdminReceiptFilters } from "@/features/receipts/types";

const PAGE_SIZE = 10;

type FilterState = Omit<AdminReceiptFilters, "page" | "size">;

/** The admin's receipts page: filterable table, with a detail drawer for review actions. */
export default function AdminReceiptsPage() {
  const [page, setPage] = useState(1);
  const [filters, setFilters] = useState<FilterState>({});
  const [selectedReceiptId, setSelectedReceiptId] = useState<number | null>(null);

  const { data, isLoading, isError } = useAdminReceiptsList({ page, size: PAGE_SIZE, ...filters });
  const approveMutation = useApproveReceipt();
  const rejectMutation = useRejectReceipt();

  const pageCount = data ? Math.max(1, Math.ceil(data.total / PAGE_SIZE)) : 1;
  const selectedReceipt = data?.items.find((item) => item.id === selectedReceiptId) ?? null;

  const handleFiltersChange = (next: FilterState): void => {
    setFilters(next);
    setPage(1);
  };

  const handleApprove = (receiptId: number): void => {
    approveMutation.mutate(receiptId, { onSuccess: () => setSelectedReceiptId(null) });
  };

  const handleReject = (receiptId: number, comment: string): void => {
    rejectMutation.mutate(
      { receiptId, comment },
      { onSuccess: () => setSelectedReceiptId(null) },
    );
  };

  return (
    <Stack spacing={3}>
      <PageHeader title="Receipts" description="Review and act on submitted receipts." />
      <AdminReceiptFiltersBar filters={filters} onChange={handleFiltersChange} />
      {isLoading && <LoadingState label="Loading receipts…" />}
      {isError && <Alert severity="error">Could not load receipts.</Alert>}
      {data && (
        <Paper variant="outlined" sx={{ p: 2 }}>
          <AdminReceiptsTable
            receipts={data.items}
            page={page}
            pageCount={pageCount}
            onPageChange={setPage}
            onSelectReceipt={setSelectedReceiptId}
          />
        </Paper>
      )}
      <ReceiptDetailDrawer
        receipt={selectedReceipt}
        onClose={() => setSelectedReceiptId(null)}
        onApprove={handleApprove}
        onReject={handleReject}
        isApproving={approveMutation.isPending}
        isRejecting={rejectMutation.isPending}
      />
    </Stack>
  );
}
