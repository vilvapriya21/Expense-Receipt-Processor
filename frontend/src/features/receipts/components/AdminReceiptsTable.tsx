import {
  Box,
  Pagination,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
} from "@mui/material";

import { EmptyState } from "@/components/EmptyState";
import { formatCurrency, formatDate } from "@/utils/formatters";

import type { Receipt } from "../types";
import { StatusChip } from "./StatusChip";

/** Props for {@link AdminReceiptsTable}. */
export interface AdminReceiptsTableProps {
  /** The receipts to display, already filtered and paginated by the caller. */
  receipts: Receipt[];
  /** The current 1-based page number. */
  page: number;
  /** Total number of pages available. */
  pageCount: number;
  /** Called with the new page number when the user changes pages. */
  onPageChange: (page: number) => void;
  /** Called with a receipt's id when its row is clicked, to open its detail drawer. */
  onSelectReceipt: (receiptId: number) => void;
}

/** A table of all receipts (admin view), opening a detail drawer on row click. */
export function AdminReceiptsTable({
  receipts,
  page,
  pageCount,
  onPageChange,
  onSelectReceipt,
}: AdminReceiptsTableProps) {
  if (receipts.length === 0) {
    return (
      <EmptyState
        message="No receipts match these filters"
        hint="Try widening the status, employee, category, or date range."
      />
    );
  }

  return (
    <Box>
      <TableContainer>
        <Table aria-label="All receipts">
          <TableHead>
            <TableRow>
              <TableCell>Employee</TableCell>
              <TableCell>Merchant</TableCell>
              <TableCell>Date</TableCell>
              <TableCell>Total</TableCell>
              <TableCell>Status</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {receipts.map((receipt) => (
              <TableRow
                key={receipt.id}
                hover
                onClick={() => onSelectReceipt(receipt.id)}
                sx={{ cursor: "pointer" }}
              >
                <TableCell>{receipt.ownerName}</TableCell>
                <TableCell>{receipt.merchantName ?? receipt.originalFilename}</TableCell>
                <TableCell>{formatDate(receipt.receiptDate)}</TableCell>
                <TableCell>{formatCurrency(receipt.totalAmount, receipt.currency)}</TableCell>
                <TableCell>
                  <StatusChip status={receipt.status} />
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
      {pageCount > 1 && (
        <Box sx={{ display: "flex", justifyContent: "center", mt: 2 }}>
          <Pagination
            count={pageCount}
            page={page}
            onChange={(_event, value) => onPageChange(value)}
          />
        </Box>
      )}
    </Box>
  );
}
