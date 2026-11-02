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
import { useNavigate } from "react-router-dom";

import { EmptyState } from "@/components/EmptyState";
import { ROUTES } from "@/constants/routes";
import { formatCurrency, formatDate } from "@/utils/formatters";

import type { Receipt } from "../types";
import { StatusChip } from "./StatusChip";

/** Props for {@link ReceiptsTable}. */
export interface ReceiptsTableProps {
  /** The receipts to display, already paginated by the caller. */
  receipts: Receipt[];
  /** The current 1-based page number. */
  page: number;
  /** Total number of pages available. */
  pageCount: number;
  /** Called with the new page number when the user changes pages. */
  onPageChange: (page: number) => void;
}

/** A table of the user's own receipts, with status chips and page navigation. */
export function ReceiptsTable({ receipts, page, pageCount, onPageChange }: ReceiptsTableProps) {
  const navigate = useNavigate();

  if (receipts.length === 0) {
    return <EmptyState message="No receipts found" hint="Receipts you upload will appear here." />;
  }

  return (
    <Box>
      <TableContainer>
        <Table aria-label="My receipts">
          <TableHead>
            <TableRow>
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
                onClick={() => navigate(ROUTES.employeeReview(receipt.id))}
                sx={{ cursor: "pointer" }}
              >
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
